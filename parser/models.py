from peewee import *
import datetime

psql_db = PostgresqlDatabase('csgo_cases', user='postgres', password='changeme', host='localhost')

class BaseModel(Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = psql_db


class Case(BaseModel):
    img_url = CharField()
    img = BlobField(null=True)
    name = CharField(unique=True)


class WeaponQualityType(BaseModel):
    name = CharField(unique=True)


class Weapon(BaseModel):
    case = ForeignKeyField(Case, backref='weapons')
    is_stattrack_available = BooleanField()
    img_url = CharField()
    img = BlobField(null=True)
    type = ForeignKeyField(WeaponQualityType, backref='weapon_qualities')


class WeaponPrice(BaseModel):
    factory_new = CharField(),
    minimal_wear = CharField(),
    field_tested = CharField(),
    well_worn = CharField(),
    battle_scarred = CharField()


class WeaponPriceType(BaseModel):
    name = CharField(unique=True)


class WeaponPriceFormations(BaseModel):
    type = ForeignKeyField(WeaponPriceType, backref='weapon_price_formations')
    weapon = ForeignKeyField(Weapon, backref='weapon_price_formations')
    price = ForeignKeyField(WeaponPrice, backref='weapon_price_formations')


if __name__ == '__main__':
    psql_db.connect()

    tables = [
        Case, 
        Weapon, 
        WeaponQualityType, 
        WeaponPrice, 
        WeaponPriceType,
        WeaponPriceFormations
    ]

    psql_db.drop_tables(tables)
    psql_db.create_tables(tables)

    WeaponPriceType.create(name='Default')
    WeaponPriceType.create(name='StatTrack')
    WeaponPriceType.create(name='Souvenir')

    WeaponQualityType.create(name='consumer_grade')
    WeaponQualityType.create(name='industrial_grade')
    WeaponQualityType.create(name='mil_spec')
    WeaponQualityType.create(name='restricted')
    WeaponQualityType.create(name='classified')
    WeaponQualityType.create(name='covert')
    WeaponQualityType.create(name='knives')
    WeaponQualityType.create(name='gloves')
    WeaponQualityType.create(name='contraband')
    WeaponQualityType.create(name='unknown')



