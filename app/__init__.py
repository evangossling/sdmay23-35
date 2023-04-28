from flask import Flask, render_template, request
from flask_mysqldb import MySQL
import paramiko

import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')

def create_app():
    app = Flask(__name__)

    app.config['MYSQL_HOST'] = 'HOST'
    app.config['MYSQL_USER'] = 'USER'
    app.config['MYSQL_PASSWORD'] = 'PASSWORD'
    app.config['MYSQL_DB'] = 'DATABASE'

    mysql = MySQL(app)

    #_______________________Pages_______________________

    # Home Page
    @app.route('/')
    def home():
        return render_template("home.html")
    

    # Query Page
    @app.route('/model')
    def model():     
        return render_template("model.html", list=list)

    #________________________API________________________

    @app.route('/paperNameAutocomplete')
    def paperNameAutocomplete():
        """endpoint for returning a list of suggested paper names in database"""
        suggestions = []
        search_term = request.args.get('term', default="", type= str)

        # SQL query
        size = 20
        cursor = mysql.connection.cursor()
        # cursor.execute("SELECT * FROM aps_dataset.papers WHERE title LIKE '%" + str(search_term) + "%' LIMIT 0, " + str(size) + ";")
        cursor.execute("SELECT * FROM aps_dataset.papers WHERE title LIKE %s LIMIT 0, " + str(size) + ";", ("%" + search_term + "%",))
        results = cursor.fetchall()    

        column_names = tuple( [column[0] for column in cursor.description] )

        # create suggestion list
        for result in results:
            # create row object as a dictionary
            row = dict(zip(column_names, result))

            # add specified field to suggestion list
            suggestions.append(row['title'])

        cursor.close()

        return suggestions
    

    @app.route('/query', methods=['POST'])
    def query():
        title = request.json.get('title')
        predictions = int(request.json.get('predictions'))
        time = float(request.json.get('time'))

        num_to_fetch = int(predictions/5)
        num_options = predictions*time
        arr = np.array([time])
        tmp = time
        for i in np.arange (time*2, num_options+time, time):
                tmp += time
                arr = np.append(arr, [tmp])
        
        print(arr)

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT ID FROM aps_dataset.papers WHERE title IN (\'"+ str(title) +"\');")
        paper_id = cursor.fetchone()
        cursor.close()

        txt_id = int(paper_id[0] / 16000)
        paper_id = paper_id[0] % 16000

        user = "USER"
        host = "HOST"
        password = "PASSWORD"

        session = paramiko.SSHClient()

        session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        session.connect(hostname=host, username=user, password=password)

        citation_count_int = np.array([])

        # execute script with parameters
        # stdin, stdout, stderr = session.exec_command('echo \"\nthis is an echo: \n\ttitle=' + str(title) + '\n\tpredictions=' + str(predictions) + '\n\ttime=' + str(time) + '\"')
        for i in range(num_to_fetch):
            stdin, stdout, stderr = session.exec_command('awk \'NR=='+str(paper_id)+'\' /home/vm-user/codes/HINTS_code/result/aps_test_test_beta_0.5num_'+str(txt_id+i)+'.txt')
            output = stdout.read().decode()
            citation_count_str = output.split(' ', -1)
            citation_count_int = np.append(citation_count_int, [eval(i) for i in citation_count_str])
        session.close()

        print(citation_count_int)

        x = np.array(arr)
        y = np.array(citation_count_int)
    
        plt.scatter(x, y)
        plt.xlabel('Time (years)')
        plt.ylabel('Predicted # of Citations')

        # Save the figure in the static directory
        plt.savefig('app/static/images/plot.png')
    
        # Close the figure to avoid overwriting
        plt.close()

        # query database for locations from title(s) and send locations to Visualizations Page
        papers = list()
        papers.append(title)

        #
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT doi FROM aps_dataset.papers WHERE title IN (\'" + str(title) + "\');")
        # cursor.execute("SELECT doi FROM papers WHERE title = %s", (str(title)))
        doi = cursor.fetchone()
        # add cited paper titles to this list
        cursor.execute("SELECT title FROM aps_dataset.papers WHERE doi IN (SELECT citing_doi FROM sdmay35.aps_citations WHERE cited_doi IN (\'" + str(doi[0]) + "\'));")
        data = cursor.fetchall()
        for i in data:
            papers.append(i[0])
        cursor.close()

        # create list of paper_names for SQL query
        paper_names = "'" + "', '".join(papers) + "'"

        locations = []
        cursor = mysql.connection.cursor()
        # use the title to get the paperID to get the placeID to get the location
        cursor.execute("SELECT name FROM aps_dataset.places WHERE id IN (select placeID FROM aps_dataset.paper_place WHERE paperID IN (select ID FROM aps_dataset.papers WHERE title IN ("+ str(paper_names) +") ));")
        data = cursor.fetchall()
        for i in data:
            locations.append(i[0])
        cursor.close()    
          
        return render_template("view.html", locations=locations)

    return app
