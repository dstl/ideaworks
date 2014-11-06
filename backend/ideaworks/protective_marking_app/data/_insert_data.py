
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

'''
Inserts data into the protective marking database.
'''
import sys
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# Append the main ideaworks directory
is_directory = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'ideaworks')
sys.path.append(is_directory)

# Access the document models
from documents import Classification
from documents import CssStyle
from documents import Descriptor
from documents import Codeword
from documents import NationalCaveat


# Fields to exclude from different aspects of the PM
gen_exclude_keys = ['inserted']
cls_exclude_keys = gen_exclude_keys + ['css_style']

def find_files(file_name_prefix):
    """ Find files matching this prefix so that new files can be dropped in"""
    
    files_to_process = []
    
    for f in os.listdir(current_dir):
        if f.startswith(file_name_prefix) == True:
            files_to_process.append(os.path.join(current_dir,f))
    
    return files_to_process

#-----------------------------------------------------------------------------

def open_and_read_data_file(file_name):
    
    if os.path.exists(file_name) == True:
        print '\tAccessing data from:\n\t%s'%(file_name)
        f = open(file_name, 'r')
    else:
        print '\t'+'*'*30
        print '\File does not exist: \n\t%s' %(file_name)
        print
        
    try:
        data = json.loads(f.read())
        print '\tRead content from file.'
    except Exception, e:
        print '\t'+'*'*30
        print '\tFailed to read data from file:\n\t%s'%(file_name)
        print
        
    return data

#-----------------------------------------------------------------------------

def handle_css(record, css_field='css_style'):
    """ Deal with logic specific to css associated with a classification"""
    
    # Deal with css_style
    if record.has_key(css_field) and isinstance(record[css_field], dict):
        col = CssStyle()
        
        # Loop any fields in the css, assuming they are in the document definition already
        for key in record[css_field].keys():
            col[key] = record[css_field][key]
        
    else:
        col = None 

    return col

#-----------------------------------------------------------------------------

def insert_data(object_template, file_name_prefix):
    """ Insert descriptor content into the db """

    print '-'*30
    print 'PROCESSING: %s'%(str(object_template.__name__))
    print
  
    # A list of dicts that need to be inserted
    records_to_insert = []
    
    # Find the files prefixed correctly that should be inserted
    files = find_files(file_name_prefix)
    for f in files:
        records_to_insert += open_and_read_data_file(f)
    
    success, failed = 0, 0
    for record in records_to_insert:
    
        # Create a new classification object
        new_object = object_template()
        
        # Build the relevant keys
        for fld in record.keys():
            if fld in cls_exclude_keys:
                continue
            new_object[fld] = record[fld]
        
        # Deal with css_style
        col = handle_css(record) 
        if col:
            new_object['css_style']=col
    
        try:
            new_object.save()
            success += 1
        except Exception, e:
            failed += 1
            print '*'*30
            print 'Failed to insert record:\n%s' %(json.dumps(record, indent=2))
            print e
            print
    
    print ''
    print 'Successful inserts: %s' %(success)
    print 'Failed inserts:     %s' %(failed)
    print ''

'''
///////////////////////////////////////////////////////////////////////////////////////////

Before running this service, modify the documents.py file to include a pointer to the 
mongo database. Change the combination of the folllowing lines (in documents.py) so that
it connects to the correct database.

I've commented them because if they aren't commented, running tests will over write the 
entire database, resulting in loss of existing data.

#MONGO_DATABASE_NAME = 'ideaworks'
#MONGO_DB_PORT = 27348
#MONGO_DB_HOST = 'ds027348.mongolab.com'
#MONGO_DB_USER = 'ideaworks'
#MONGO_DB_PASS = 'ideaworks'
#register_connection(alias='default',name=MONGO_DATABASE_NAME, host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USER, password=MONGO_DB_PASS)
#register_connection(alias='default',name=MONGO_DATABASE_NAME)

///////////////////////////////////////////////////////////////////////////////////////////
'''


#//////////////////////////////////////////////////
# CLASSIFICATIONS
# Clear the db, then insert new
Classification.objects.all().delete()
insert_data(object_template=Classification, file_name_prefix='classifications')

#//////////////////////////////////////////////////
# DESCRIPTORS
# Clear the db, then insert new
Descriptor.objects.all().delete()
insert_data(object_template=Descriptor, file_name_prefix='descriptors')


#//////////////////////////////////////////////////
# CODEWORDS
# Clear the db, then insert new
Codeword.objects.all().delete()
insert_data(object_template=Codeword, file_name_prefix='codewords')

#//////////////////////////////////////////////////
# NATIONAL CAVEATS
# Clear the db, then insert new
NationalCaveat.objects.all().delete()
insert_data(object_template=NationalCaveat, file_name_prefix='national_caveats')
