# -*- coding: utf-8 -*-
"""
Created on Mon Feb  7 15:29:54 2022

@author: ZZ06PQ740
"""

#%%
import argparse
import sys
from sys import argv
import pandas as pd
import numpy as np

#%%

#handling the command line argument parsing
parser = argparse.ArgumentParser()
parser.add_argument('input_file')
parser.add_argument('orig')
parser.add_argument('dest')
parser.add_argument('-b', '--bags', type=int)

args = parser.parse_args()

#%%


"""
This part checks the (sys.arg) input parameters.
    input_file must be specified and should exist in the directory where .py is.
        
    input_file : str
        File name of the input file (must be in the same directory).
    orig : str 
        Origin Airport
    dest : str
        Destionation Airport
    bags : int,  default = 0
        optional parameter, number of bags 
    return : boolean, default=False
        optional parameter, is it a return flight?
        

parameter_dict: dict
   dictionary containing all valid parameters
"""

global parameter_dict
parameter_dict = {}
parameter_list = [
        'input_file', 
        'orig',
        'dest',
        'bags'#,
        #'return'
]
for user_input in argv[1:]: 
        if sys.argv[1].split('.')[-1][:3] == 'csv':
            parameter_dict['input_file'] = sys.argv[1]
        else: 
            sys.exit("The first parameter is missing, check it please!")
        
        df=pd.read_csv(parameter_dict['input_file']) 
        
        if sys.argv[2]  in df['origin'].values:
            parameter_dict['orig'] = sys.argv[2]
        else: 
            sys.exit("The given origin is not in the list, check it please!")

        if sys.argv[3]  in df['destination'].values:
            parameter_dict['dest'] = sys.argv[3]
        else: 
            sys.exit("The given destination is not in the list, check it please!")
        
        if args.bags!=None:
            parameter_dict['bags']=args.bags
        else:     
            parameter_dict['bags']=0
        
            
parameter_dict = {param: parameter_dict[param] for param in parameter_list}
print("Parameters: ",parameter_dict ,"\n")
    
    
#%%

#avoid warnings
pd.options.mode.chained_assignment = None

#%%

"""
The core of the process:
looking for direct and indirect connenctions between origin and destination, 
filtering with the time constraint based on layover time rule
"""


#left join
df_left = df.loc[(df['origin']==parameter_dict['orig'])].merge(df.loc[(df['destination']==parameter_dict['dest'])], 
   left_on='destination', right_on='origin', how='left',
   suffixes=('_left', '_right'))

#convert str->date
df_left['departure_right'] = pd.to_datetime(df_left['departure_right']) 
df_left['arrival_left'] = pd.to_datetime(df_left['arrival_left'])

df_left['departure_left'] = pd.to_datetime(df_left['departure_left']) 
df_left['arrival_right'] = pd.to_datetime(df_left['arrival_right'])

#add new col time difference
df_left['time_diff']=(df_left['departure_right']-df_left['arrival_left'])
df_left['time_diff_hour']=df_left['time_diff']/np.timedelta64(1, 'h')

df_left.to_excel("result.xlsx") 

#filter for time (layover time in B should not be less than 1 hour and more than 6 hours)
df_filt=df_left.loc[(df_left['time_diff_hour']>=1) & (df_left['time_diff_hour']<=6)
                    | (df_left['time_diff_hour'].isnull()==True)]

#df_filt.to_excel("result_filtered.xlsx") 


#calculate summarizing cols
df_filt['bags_allowed']=df_filt[['bags_allowed_left', 'bags_allowed_right']].apply(lambda x: min(x[0],x[1]), axis=1)
df_filt['destination']=parameter_dict['dest'] 
df_filt['origin']=parameter_dict['orig']
df_filt['bags_count']=parameter_dict['bags']

df_filt['total_price']=np.where(pd.isnull(df_filt['base_price_right']),df_filt['base_price_left']+(parameter_dict['bags']*df_filt['bag_price_left']),
    df_filt['base_price_left']+(parameter_dict['bags']*df_filt['bag_price_left'])+df_filt['base_price_right']+(parameter_dict['bags']*df_filt['bag_price_right']))

df_filt['travel_time']=np.where(pd.isnull(df_filt['base_price_right']),(df_filt['arrival_left']-df_filt['departure_left']), 
    (df_filt['arrival_right']-df_filt['departure_left']))

#extract time in h:m:s format
df_filt['travel_time'] = df_filt['travel_time'].apply(lambda x: (pd.datetime.min + x).time())

#df_filt.to_excel("result_filtered.xlsx") 

#%%

"""
Prepare columns to meet the json format
"""


#concat relevant cols
df_filt['final_col1'] = df_filt.apply(lambda row: {'flight_no':row['flight_no_left'],
                                            'origin':row['origin_left'],
                                            'destination':row['destination_left'],
                                            'departure':row['departure_left'],
                                            'arrival':row['arrival_left'],
                                            'base_price':row['base_price_left'],
                                            'bag_price':row['bag_price_left'],
                                            'bags_allowed':row['bags_allowed_left']
                                            },
                            axis=1)

df_filt['final_col2']= df_filt.apply(lambda row: {'flight_no':row['flight_no_right'],
                                            'origin':row['origin_right'],
                                            'destination':row['destination_right'],
                                            'departure':row['departure_right'],
                                            'arrival':row['arrival_right'],
                                            'base_price':row['base_price_right'],
                                            'bag_price':row['bag_price_right'],
                                            'bags_allowed':row['bags_allowed_right']
                                            },
                            axis=1)

#df_filt.to_excel("result_filtered.xlsx") 


#concat dictionaries, if 2 flights
cols = ['final_col1', 'final_col2']
df_filt['flights'] = np.where(pd.isnull(df_filt['base_price_right']),
                           df_filt['final_col1'],
                           df_filt[cols].apply(lambda row: ','.join(row.values.astype(str)), axis=1))

#adding brackets
df_filt['flights'] = '[' + df_filt['flights'].astype(str)+']'


#filter for relevant cols again
df_final=df_filt[['flights','bags_allowed', 'bags_count', 'destination', 'origin', 'total_price', 'travel_time']]

#order by price
df_final=df_final.sort_values(by='total_price')


df_final.to_excel("result_filtered2.xlsx") 


#%%
"""
Extract result in json format
"""

json_records = df_final.to_json(orient ='records')

#change double quotes
json_records=json_records.replace(':"[', ':[')
json_records=json_records.replace('}]"', '}]')

print("json_records = ", json_records, "\n")

