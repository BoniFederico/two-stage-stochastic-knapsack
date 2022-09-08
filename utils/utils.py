import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import six
 
def from_dict_to_csv(list_of_dictionaries,file_name):
      
    with open(file_name+".csv", 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = list_of_dictionaries[0].keys())
        writer.writeheader()
        writer.writerows(list_of_dictionaries)

#https://stackoverflow.com/questions/26678467/export-a-pandas-dataframe-as-a-table-image
def from_dataframe_to_table(data, col_width=3.0, row_height=0.625, font_size=14,
                     header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                     bbox=[0, 0, 1, 1], header_columns=0,
                     ax=None, **kwargs):
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off');

    mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs);

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in  six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight='bold', color='w')
            cell.set_facecolor(header_color)
        else:
            cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
    return ax

def from_list_to_csv(file_name,list):
        with open(file_name ,'w') as f:
                write=csv.writer(f)
                write.writerows([[e] for e in list])
                
def from_csv_to_list(file_name):
        with open(file_name,newline='') as f:
                data=csv.reader(f)
                return [(el[0]) for el in list(data) if len(el)>0]