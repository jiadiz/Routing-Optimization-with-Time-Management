#!/usr/bin/env python
# coding: utf-8

# In[45]:


import pickle
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


# In[46]:


with open('C:/Users/jiadiz/Desktop/PGT Trucking/initial model/Github/create_dashboard.pkl', 'rb') as f:
    dashboard_materials = pickle.load(f)


# In[51]:


routes,first_wave,ds = dashboard_materials


# In[52]:


def create_dashboard(routes,first_wave,ds):
    new_df=pd.DataFrame(routes,columns=["Label"])
    new_df=new_df["Label"].str.split(":", n = 1, expand = True)
    new_df.columns=["Driver Name","L2"]
    newdf_split=new_df["L2"].str.split("->", expand = True)
    columnnames = {}

    count = 0

    for i in newdf_split.columns:

      count += 1
      if i==0:
            count=0
            columnnames[i]=f"Home Depot"
      else:
            columnnames[i] = f"JOB{count}"
    newdf_split.rename(columns = columnnames ,inplace = True)
    new_df=pd.concat([new_df,newdf_split],axis=1)
    new_df.drop(columns=["L2"],inplace=True)
    pd.set_option('display.max_rows', 500)
    pivoted_df=new_df.melt(id_vars=['Driver Name'], var_name='Job Number', value_name='Job Code')
    pivoted_df=pivoted_df[pivoted_df["Job Code"].str.contains("None") == False]
    pivoted_df=pivoted_df.sort_values(by=['Driver Name','Job Number'])
    pivoted_df['Job Number'] = np.where(pivoted_df['Job Code'].str.startswith('T'), 'Home Depot', pivoted_df['Job Number'])
    pivoted_df.reset_index(drop=True, inplace=True)
    first_wave['order_id'] = first_wave['order_id'].astype(str)
    df_depot = pd.merge(pivoted_df, first_wave,
                           how='left', left_on=['Driver Name','Job Code'], right_on=['driver_id','order_id'])
    df_depot=df_depot[['Driver Name', 'Job Number','Job Code','origin_zipcode','dest_zipcode','depot_zipcode','dest_lat','dest_lng','origin_lat','origin_lng','depot_lat','depot_lng']]
    df_depot_new = pd.merge(df_depot, ds,
                           how='left', left_on=['Job Code'], right_on=['terminals'])
    df_depot_new=df_depot_new[['Driver Name', 'Job Number','Job Code','depot_zipcode_x','depot_zipcode_y','origin_zipcode','dest_zipcode']]
    df_depot_new['depot_zipcode_y'].fillna(value=df_depot_new['depot_zipcode_x'],inplace=True)
    df_depot_new.drop('depot_zipcode_x',axis=1,inplace=True)
    abc=df_depot_new
    abc['origin_zipcode'].fillna(value=abc['depot_zipcode_y'],inplace=True)
    abc['dest_zipcode'].fillna(value=abc['depot_zipcode_y'],inplace=True)
    a=len(abc)
    a
    for i,row in abc.iterrows():
        if i==0:
            row['dest_zipcode']=abc.loc[i+1]['origin_zipcode']
        elif i>0 and i!=(a-1) and row['Job Code'].startswith('T') and abc.loc[i+1]['Job Code'].startswith('T'):
            row['origin_zipcode']=abc.loc[i-1]['dest_zipcode']
        elif i>0 and i!=(a-1) and row['Job Number'].startswith('H') and abc.loc[i+1]['Job Number'].startswith('J'):
            row['dest_zipcode']=abc.loc[i+1]['origin_zipcode']
        elif i==a-1:
            row['origin_zipcode']=abc.loc[i-1]['dest_zipcode']
    abc.drop('depot_zipcode_y',axis=1,inplace=True)
    df1 = abc
    dflen=len(df1)
    df2 = pd.DataFrame(columns=['Driver Name', 'Job Number', 'Job Code', 'origin_zipcode', 'dest_zipcode'])

    for i, row in df1.iterrows():
        if i==(dflen-1) and df1.loc[i]['Job Number'] == 'Home Depot':
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': 'Travel back to Home Depot', 
                              'Job Code': row['Job Code'], 'origin_zipcode': row['origin_zipcode'], 
                              'dest_zipcode': row['dest_zipcode']}, ignore_index=True)
        elif df1.loc[i]['Job Number'] == 'Home Depot' and df1.loc[i+1]['Job Number'].startswith('J') and i!=dflen-1:
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': 'Travel from Home Depot', 
                              'Job Code': row['Job Code'], 'origin_zipcode': row['origin_zipcode'], 
                              'dest_zipcode': row['dest_zipcode']}, ignore_index=True)
        elif df1.loc[i]['Job Number'] == 'Home Depot' and df1.loc[i+1]['Job Number']=='Home Depot' and i!=dflen-1:
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': 'Travel back to Home Depot', 
                              'Job Code': row['Job Code'], 'origin_zipcode': row['origin_zipcode'], 
                              'dest_zipcode': row['dest_zipcode']}, ignore_index=True)
        elif df1.loc[i+1]['Job Number'].startswith('H') and df1.loc[i]['Job Number'].startswith('J') and i!=dflen-1:
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': row['Job Number'], 
                              'Job Code': row['Job Code'], 'origin_zipcode': row['origin_zipcode'], 
                              'dest_zipcode': row['dest_zipcode']}, ignore_index=True)
        else:
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': row['Job Number'], 
                              'Job Code': row['Job Code'], 'origin_zipcode': row['origin_zipcode'], 
                              'dest_zipcode': row['dest_zipcode']}, ignore_index=True)
            df2 = df2.append({'Driver Name': row['Driver Name'], 'Job Number': 'Travel to the next Job', 
                              'Job Code': 'Travel', 'origin_zipcode': row['dest_zipcode'], 
                              'dest_zipcode': df1.iloc[i+1]['origin_zipcode']}, ignore_index=True)
    from uszipcode import SearchEngine

    search = SearchEngine()

    for index, row in df2.iterrows():
        origin_zip = row['origin_zipcode']
        dest_zip = row['dest_zipcode']
    
        origin_lat = search.by_zipcode(origin_zip).lat
        origin_lon = search.by_zipcode(origin_zip).lng
        dest_lat = search.by_zipcode(dest_zip).lat
        dest_lon = search.by_zipcode(dest_zip).lng
    
        df2.loc[index, 'origin_lat'] = origin_lat
        df2.loc[index, 'origin_lon'] = origin_lon
        df2.loc[index, 'dest_lat'] = dest_lat
        df2.loc[index, 'dest_lon'] = dest_lon
    df2.rename(columns = {'origin_zipcode':'Start_Zip','dest_zipcode':'End_Zip','origin_lat':'Start_Lat','origin_lon':'Start_Long','dest_lat':'End_Lat','dest_lon':'End_Long'}, inplace = True)
    import folium
    import ipywidgets as widgets

    data = df2

    driver_names = data['Driver Name'].unique().tolist()

    print('Select a Driver from the below Dropdown:')
    driver_dropdown = widgets.Dropdown(options=driver_names,description='Driver Name:')

    def update_map(driver):
        map = folium.Map(location=[data["Start_Lat"][0], data["Start_Long"][0]], zoom_start=6)
        driver_data = data[data['Driver Name'] == driver]
        count=0
        for index, row in driver_data.iterrows():
            if row["Job Number"].startswith("JOB"):
                count=count+1
                folium.Marker(
                    location=[row["Start_Lat"], row["Start_Long"]],
                    popup="JOB START LOCATION", 
                    icon=folium.Icon(color='blue',icon="truck",prefix="fa"),
                    tooltip=['Driver Name:',row['Driver Name'],row['Job Number'],"JOB ID:",row['Job Code'],"ZIPCODE:",row['Start_Zip']]
                ).add_to(map)
                folium.Marker(
                    location=[row["End_Lat"], row["End_Long"]],
                    popup="JOB END LOCATION", 
                    icon=folium.Icon(color='pink',icon="truck-pickup",prefix="fa"),
                    tooltip=['Driver Name:',row['Driver Name'],row['Job Number'],"JOB ID:",row['Job Code'],"ZIPCODE:",row['End_Zip']]
                ).add_to(map)
            else:
                folium.Marker(
                    location=[row["End_Lat"], row["End_Long"]],
                    popup="HOME DEPOT", 
                    icon=folium.Icon(color='red',icon="house",prefix="fa"),
                    tooltip=['Driver Name:',row['Driver Name'],"Home Depot","ZIPCODE:",row['Start_Zip']]
                ).add_to(map)

            if row["Job Number"].startswith("JOB"):
                folium.PolyLine(
                locations=[(row["Start_Lat"], row["Start_Long"]), (row["End_Lat"], row["End_Long"])],
                color='red',
                tooltip=row['Job Number'],weight=5 ).add_to(map)
            else:
                folium.PolyLine(locations=[(row["Start_Lat"], row["Start_Long"]), (row["End_Lat"], row["End_Long"])],
                color='blue',
                tooltip=row['Job Number'],
                dash_array='10'
                ).add_to(map)
           
            legend_html = '''
            <div style="position: fixed; border: 3px solid red;
                     width: 150px ; height: 90px; 
                     z-index:9999; font-size:10px ;
                     text-align:center; font-family:verdana;
                     background-color: white;
                     "><b>Marker Legend</b><br>
                      &nbsp; <i>Home Depot:</i> &nbsp; 
                      <i class="fa fa-solid fa-house fa-2x" style="color:red"></i><br>
                      &nbsp; <i>Job Start Location:</i> &nbsp; 
                      <i class="fa fa-solid fa-truck fa-2x" style="color:DeepSkyBlue"></i><br>
                      &nbsp; <i>Job End Location:</i> &nbsp; 
                      <i class="fa fa-solid fa-truck-pickup fa-2x" style="color:pink"></i>
            </div>
            '''
        print("Number of Jobs:",count) 
        map.get_root().html.add_child(folium.Element(legend_html))
        display(map)

# Call the update_map function when the dropdown value changes
    return widgets.interact(update_map, driver=driver_dropdown)


# In[53]:


create_dashboard(routes,first_wave,ds)

