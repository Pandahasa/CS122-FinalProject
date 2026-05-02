import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def recommend_tee(handicap, tee_box_df):
    tees = tee_box_df.groupby("Tee Box Name").first().sort_values(by='Tee Slope Rating', ascending=False)
    avg_slope = np.mean(tees['Tee Slope Rating'].values)

    if handicap <= 10:
        return tees.index[0]
    
    elif handicap <= 18:
    # Use avg_slope as a threshold
        if avg_slope > 135:
            return tees.index[len(tees) // 2 + 1]  # step down if course is especially hard
        return tees.index[len(tees) // 2]
        
    else:
        return tees.index[-1]
    
def give_motivation(handicap):

    if handicap <= 10:
        return "The iconic Sam Snead once said: 'forget your opponents; always play against par.' " \
        "There are only 4 things that matter: you, the golf ball, the course, and your thoughts"
    
    elif handicap <= 18:
        return "Congrats on your progress in this wonderful game! The only way from here is up. " \
        "You'll be playing from the tips in no time!"
    
    else:
        return "Golf rewards patience above all else. " \
        "Every round is a new opportunity. Keep grinding — the game always gives back what you put in"

def yardage_chart(course_data, tee_box):

    # Read the course data into a dataframe
    golf_df = pd.read_csv(course_data)

    # We only care about the data under the specified tee box
    selected_tee_box_df = golf_df[golf_df['Tee Box Name'] == tee_box]

    # Sort the holes by the hole number to access the yardage and par information
    hole_num_sorted = selected_tee_box_df.sort_values(by='Hole Number')
 
    # Store the yardages and par values into a series
    yardages = hole_num_sorted['Yardage']
    pars = hole_num_sorted['Par']

    # Convert hole number list (goes from [1, 2, 3] -> [H1, H2, H3])
    final_hole_list = []
    holes = hole_num_sorted['Hole Number']

    for hole in holes:
        final_hole_list.append('H' + str(hole))


    # Map the par to color. 
    par_to_color = {}
    par_to_color[3] = 'Green' 
    par_to_color[4] = 'Blue' 
    par_to_color[5] = 'Orange' 

    final_color_list = []
    for par in pars:
        final_color_list.append(par_to_color.get(par, 'Gray'))

    fig, ax = plt.subplots(figsize=(10, 8))
    plt.barh(final_hole_list, yardages, color=final_color_list)
    plt.gca().invert_yaxis()

    for i, yardage in enumerate(yardages):
        plt.text(yardage / 2, i, str(yardage), va='center', ha='center', color='white', fontweight='bold')


    #   Add a title — plt.title()
    course_name = golf_df['Course Name'].iloc[0]

    plt.title(f"Yardage Profile - {course_name}")

    # Sublabel under title giving the key course info
    total_yards = int(yardages.sum())
    par_total = int(pars.sum())
    plt.title(f"Yardage Profile - {course_name}\n{tee_box} Tees · Par {par_total} · {total_yards:,} yards", fontsize=12)

    # Add x-axis label
    plt.xlabel("Yardages")
     

    # Add x-axis label
    # Add legend for par colors
    legend_elements = [
        Patch(facecolor='Green', label='Par 3'),
        Patch(facecolor='Blue', label='Par 4'),
        Patch(facecolor='Orange', label='Par 5')
    ]

    plt.legend(handles=legend_elements)


    # Save to static folder — plt.savefig()
    plt.savefig(f"static/{course_name}_yardage_breakdown.png")

    plt.close()

    # Return the filename
    return f"static/{course_name}_yardage_breakdown.png"
    

    
