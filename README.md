remodel
=======

[![Build Status](https://travis-ci.org/linkyndy/remodel.svg?branch=master)](https://travis-ci.org/linkyndy/remodel)

Very simple yet powerful and extensible Object Document Mapper for RethinkDB, written in Python.

## It is plain simple!

```python
from remodel.models import Model

class User(Model):
    pass
```

That's really everything you need to do to set up a model!

> Don't forget to turn on your RethinkDB server and to create your tables (check the examples below for a helper that does just that!).

## Features

- schemaless;
- `dict` interface;
- full support for relations;
- indexes;
- convention over configuration;
- lazy-loading;
- caching;
- thoroughly tested;

## Installation

```bash
pip install remodel
```

## Examples

### Basic CRUD operations

```python
class Order(Model):
    pass

# Create
my_order = Order.create(customer='Andrei', shop='GitHub')
# Update
my_order['total'] = 100
my_order.save()
# Read
saved_order = Order.get(customer='Andrei')
# Delete
saved_order.delete()
```

### Creating tables

```python
from remodel.models import Model
from remodel.helpers import create_tables, create_indexes

class Party(Model):
    has_many = ('Guest',)

class Guest(Model):
    belongs_to = ('Party',)

# Creates all database tables defined by models
create_tables()
# Creates all table indexes based on model relations
create_indexes()
```

### Configuring database connection

Setups are widely different, so here's how you need to configure remodel in order to connect to your RethinkDB database:

```python
from remodel.connection import pool

pool.configure(host='localhost', port=28015, auth_key=None, user='admin', password='', db='test')
```

### Relations

#### Has one / Belongs to

```python
class User(Model):
    has_one = ('Profile',)

class Profile(Model):
    belongs_to = ('User',)

andrei = User.create(name='Andrei')
profile = Profile.create(user=andrei, network='GitHub', username='linkyndy')
print profile['user']['name'] # prints Andrei
```

#### Has many / Belongs to

```python
class Country(Model):
    has_many = ('City',)

class City(Model):
    belongs_to = ('Country',)

romania = Country.create(name='Romania')
romania['cities'].add(City(name='Timisoara'), City(name='Bucharest'))
print romania['cities'].count() # prints 2
```

#### Has and belongs to many

```python
class Post(Model):
    has_and_belongs_to_many = ('Tag',)

class Tag(Model):
    has_and_belongs_to_many = ('Post',)

my_post = Post.create(name='My first post')
personal_tag = Tag.create(name='personal')
public_tag = Tag.create(name='public')
my_post['tags'].add(personal_tag, public_tag)
print my_post['tags'].count() # prints 2
```

#### Has many through

```python
class Recipe(Model):
    has_many = ('SpecificSpice',)

class Chef(Model):
    has_many = ('SpecificSpice',)

class SpecificSpice(Model):
    belongs_to = ('Recipe', 'Chef')

quattro_formaggi = Recipe.create(name='Pizza Quattro Formaggi')
andrei = Chef.create(name='Andrei')
andreis_special_quattro_formaggi = SpecificSpice.create(chef=andrei, recipe=quattro_formaggi, oregano=True, love=True)
print andreis_special_quatro_formaggi['love'] # prints True
```

### Callbacks

```python
from remodel.models import Model

class Shirt(Model):
    def after_init(self):
        self.wash()

    def wash(self):
        print 'Gotta wash a shirt after creating it...'
```

or

```python
from remodel.models import Model, after_save

class Prize(Model):
    @after_save
    def brag(self):
        print 'I just won a prize!'
```

### Custom table name

```python
class Child(Model):
    table_name = 'kids'

print Child.table_name # prints 'kids'
```

### Custom model queries

```python
import rethinkdb as r

class Celebrity(Model):
    pass

Celebrity.create(name='george clooney')
Celebrity.create(name='kate winslet')
upper = Celebrity.map({'name': r.row['name'].upcase()}).run()
print list(upper) # prints [{u'name': u'GEORGE CLOONEY'}, {u'name': u'KATE WINSLET'}]
```

### Custom instance methods

```python
class Child(Model):
    def is_minor(self):
        if 'age' in self:
            return self['age'] < 18

jack = Child.create(name='Jack', age=15)
jack.is_minor() # prints True
```

### Custom class methods

```python
from remodel.object_handler import ObjectHandler, ObjectSet

class TripObjectHandler(ObjectHandler):
    def in_europe(self):
        return ObjectSet(self, self.query.filter({'continent': 'Europe'}))

class Trip(Model):
    object_handler = TripObjectHandler

Trip.create(continent='Europe', city='Paris')
Trip.create(continent='Asia', city='Shanghai')
Trip.create(continent='Europe', city='Dublin')
print len(Trip.in_europe()) # prints 2
```

### Viewing object fields

```python
class Train(Model):
    pass

train = Train.create(nr=12345, destination='Paris', has_restaurant=True, classes=[1, 2])
print train.fields.as_dict()
# prints {u'classes': [1, 2], u'nr': 12345, u'destination': u'Paris', u'has_restaurant': True, u'id': u'd9b8d57f-5d67-4ff7-acf8-cbf7fdd65581'}
```

## Concepts

### Relations

Remodel supports various types of relationships:
- has one
- belongs to
- has many
- has and belongs to many
- has many through

#### Defining relations

Related models are passed as tuples in a model's definition. All other aspects, such as foreign keys, indexes, lazy relation loading and relation cache are magically handled for you.

If you need precise definition for your related models, you can pass a configuration tuple instead of the string name of your related model:

```python
    class Artist(Model):
        has_many = (('Song', 'songs', 'id', 'song_id'), 'Concert')
        # Tuple definition: (<related model name>, <related objects accessor field>, <model key>, <related model key>)
```

> One important thing to notice is that reverse relationships are **not automatically ensured** if only one end of the relationship is defined. This means that if ``Artist has_many Song``, ``Song belongs_to Artist`` is not automatically enforced unless explicitly defined.

#### Using relations

Assigning `has_one` and `belongs_to` objects doesn't mean that they are persisted. You need to manually call `save()` on them; assuming `Profile belongs_to User`:

```python
profile['user'] = User(...)
profile.save()
```

On the other side, assigning `has_many` and `has_and_belongs_to_many` objects automatically persist them, so there is no need for you to call `save()` on them; assuming `Shop has_many Product`:

```python
shop.add(product1, produt2)
# No need to call save() on products!
```

> Note that certain assignments of related objects can not be performed unless one (or both) of the objects is saved. You can not save a `GiftSize` with a `Gift` attached without saving the `Gift` object first (when having a `GiftSize belongs_to Gift`).

## Documentation

Can be found at https://github.com/linkyndy/remodel/wiki.

## Motivation

The main reason for Remodel's existence was the need of a light-weight ODM for RethinkDB, one that doesn't force you to ensure a document schema, one that provides a familiar interface and one that gracefully handles relations between models.

## Status

Remodel is under active development and it is not _yet_ production-ready.

## How to contribute?

Any contribution is **highly** appreciated! See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

See [LICENSE](LICENSE)
