from unicodedata import name

import duckdb
import time
from model import *


def get_brands():
    records = duckdb.sql("""
        select Id, Name from Brands
""").fetchall()

    return [Brand(r) for r in records]


def get_brand_by_name(name):
    brand_lkp = {b.Name: b for b in get_brands()}  # Create a lookup dictionary for brands to avoid repeated calls to get_brands in the loop
    return next((b for b in brand_lkp.values() if b.Name == name), Brand((0, name)))

def get_countries():
    records = duckdb.sql("""
        select distinct c.Id, c.Name , COALESCE(im.Value, 0) as Value
        from Countries c
        left join (
            select 
                 CountryId
                ,Value
                ,row_number() over(partition by CountryId order by Year desc) rn
            from ImportVolumes                       
        ) im on c.Id = im.CountryId        
        where im.rn=1 or im.rn is null
        order by c.Name
    """).fetchall()

    return [Country(r) for r in records]


def get_country_by_name(name):
    return [c for c in get_countries() if c.Name == name][0]


def get_brands_by_country_of_manufacturing():
    start = time.perf_counter()
    
    records = duckdb.sql("""
        select 
             r.Number
            ,c.Name
            ,r.Brand
        from Registrations r
        inner join Countries c 
            on r.CountryOfManufacturing = c.Id
    """).fetchall()

    countries = {}
    #registrations = [Registration(r) for r in records]  Removed as I couldn't see how it was being used.  

    country_lkp = {c.Name: c for c in get_countries()}  #Creat a lookup dictionary for countries to avoid repeated calls to get_country_by_name in the loop
    brand_lkp = {b.Name: b for b in get_brands()}  # Create a lookup dictionary for brands to avoid repeated calls to get_brand_by_name in the loop
    def get_brand_from_lookup(name):
        return brand_lkp.get(name, Brand((0, name)))
        
    for record in records:
       
        if not record[1] in countries.keys():
            countries[record[1]] = country_lkp[record[1]]
             # countries[record[1]] = get_country_by_name(record[1])

        countries[record[1]].add(Registration(record),get_brand_from_lookup)
                                    
    end = time.perf_counter()
    print(f"Execution time: {end - start:.6f} seconds")   
    return countries.values()

