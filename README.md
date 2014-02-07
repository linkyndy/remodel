=======
remodel
=======

Very simple yet powerful and extensible Object Document Mapper for RethinkDB, written in Python.

It is plain simple
==================

.. code-block:: python

    from remodel import Model
    
    class User(Model):
        pass
    
That's really everything you need to do to set up a model!


Features
========

- schemaless;
- ``dict`` interface;
- full support for relations;
- indexes;
- convention over configuration;
- lazy-loading;
- caching;

Installation
============

To install remodel, just:

.. code-block:: bash

    $ pip install remodel
    
Examples
========

Field manipulation
------------------

.. code-block:: python

    class City(Model):
        pass

    class School(Model):
        belongs_to = ('City',)
        has_many = ('Class',)
        
    class Class(Model):
        belongs_to = ('School',)
        
    >>> city = City(name='Timisoara', country='Romania')
    >>> city.save()
    >>> school = School(type='high-school', city=city)
    >>> school.save()
    >>> print school['type']
    high-school
    >>> print school['city']['name']
    Timisoara
    >>> c22 = Class(name='Class 22')
    >>> c22.save() # We can save a class even though we haven't specified the School object it belongs to!
    >>> print c22['school']
    None
    >>> c14 = Class(name='Class 14')
    >>> school['classes'].add(c22, c14) # No need to call save() on assign objects; add() takes care of it
    >>> for c in school['classes'].all():
    ...     print c['name']
    ...
    Class 14
    Class 22
    >>> Class.get(name='Class 14').delete()
    >>> print len(list(school['classes'].all())) # Since related Classes are lazily fetched, we need to coerce them to a list before returning their count
    1
    >>> school['principal'] = 'Andrei H'
    >>> del school['type']
    >>> print school.fields.as_dict()
    {'city': <City 1e03c1f1-32bd-434c-8f54-8d85a3ccb8ae>, 'principal': 'Andrei H'}
    
Handling fields is as simple as handling a standard `dict`.
    

Defining relations
------------------

.. code-block:: python

    class Artist(Model):
        has_many = ('Song', 'Concert')
        has_and_belongs_to_many = ('Genre',)
        
    class Song(Model):
        belongs_to = ('Artist',)
        
remodel supports various types of relationships:
- has one
- belongs to
- has many
- has and belongs to many
- has many through

Related models are passed as tuples in a model's definition. All other aspects, such as foreign keys, indexes, lazy relation loading and relation cache are magically handled for you.

If you need precise definition for your related models, you can pass a configuration tuple instead of the string name of your related model:

.. code-block:: python

    class Artist(Model):
        has_many = (('Song', 'songs', 'id', 'song_id'), 'Concert') # Tuple definition: (<related model name>, <related objects accessor field>, <model key>, <related model key>)
        
One important thing to notice is that reverse relationships aren't automatically ensured if only one end of the relationship is defined. This means that if ``Artist has many Song``, ``Song belongs to Artist`` is not automatically enforced unless explicitly defined. The reason for this design decision is that many relationships are accessed only from one side and by ensuring a double-sided access an unnecessary overhead is introduced. Hence, simple and more explicit results in higher performance.
    
    
Motivation
==========

The main reason for remodel's existence is the need of a light-weight ODM for RethinkDB, one that doesn't force you to ensure a document schema, one that provides a familiar interface and one that gracefully handles relations between models.
