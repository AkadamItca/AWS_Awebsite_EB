import boto3
from flask import *
#from flask import Flask, render_template, request, flash, redirect, session
from functools import wraps
from flask_s3 import FlaskS3
import json,os,folium,requests
from werkzeug import secure_filename
import pandas as pd
from azure.storage.blob import BlockBlobService
from geopy.geocoders import Nominatim
import xlrd,datetime, runpy
# Web scraping package
from selenium import webdriver
# Language Translator
from googletrans import Translator  # Import Translator module from googletrans package
import pickle
from boto3.dynamodb.conditions import Key, Attr



application = Flask(__name__)
application.secret_key = "itca1234"
application.config['FLASKS3_BUCKET_NAME'] = 'zappa-q8s9hsqwq'
s3 = FlaskS3(application)
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', aws_access_key_id = 'AKIA5QM2V3T3F7JZJA5F', aws_secret_access_key = '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')
#dynamodb = boto3.resource('dynamodb', region_name='us-east-2')

@application.route('/')
def home():
    return render_template('Home.html')
def login_required(test):
    @wraps(test)
    def  wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('Please login first')
            return redirect(url_for('home'))
    return wrap


# Route for handling the login page logic
@application.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        error = 'Invalid Credentials. Please try again.'
        if uname != '' and pwd != '':
            table = dynamodb.Table('UserValidation')
            response = table.query(
                KeyConditionExpression=Key('username').eq(uname)
            )
            if response['Items'] == []:
                Uerror = 'Invalid Username'
                return render_template('Home.html', error=Uerror)
            else:
                items = response['Items']
                print(items[0]['password'])
                if pwd == items[0]['password']:
                    session['logged_in'] = True
                    return redirect(url_for('index'))
        return render_template('Home.html', error=error)

@application.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You were logged out")
    return redirect(url_for('home'))

@application.route('/index')
@login_required
def index():
    return render_template('index.html')

@application.route('/upload')
@login_required
def upload():
   files_values = blobService()
   return render_template('service.html',radio_form=files_values)

def blobService():
    blb_names=[]
    block_blob_service = BlockBlobService(account_name='isuzupredmaintenance', account_key='jsUq8mN4NIHahxj4xOXs4tHtS62cEkGvryEZfE3H3FGtr8tQ+lf3YSaophd1kuCyyAE2257QtJreh1AV7FkQ8A==')
    container_name ='isuzu'
    generator = block_blob_service.list_blobs(container_name)
    for blob in generator:
        blb_names.append(blob.name)
    return blb_names

@application.route('/uploader', methods=['GET','POST'])
def upload_file():
   if request.method == 'POST':
      checked_files = request.form.getlist("options")
      print("checked files : ",checked_files)
      local_path='./spreadsheets'
      container_name ='isuzu'
      block_blob_service = BlockBlobService(account_name='isuzupredmaintenance', account_key='jsUq8mN4NIHahxj4xOXs4tHtS62cEkGvryEZfE3H3FGtr8tQ+lf3YSaophd1kuCyyAE2257QtJreh1AV7FkQ8A==')
      for i in checked_files:
          full_path_to_file2 = os.path.join(local_path, i)
          print("\nDownloading blob to " + full_path_to_file2)
          block_blob_service.get_blob_to_path(container_name, i, full_path_to_file2)
      print(checked_files[-1])
      wb = xlrd.open_workbook('./spreadsheets/' + checked_files[-1])
      sheet = wb.sheet_by_index(0)
      print(sheet)
      nrow=sheet.nrows
      print(sheet.cell_value(0, 0))
      lat=sheet.cell_value(nrow-1,1)
      lon=sheet.cell_value(nrow-1,2)
      temp=sheet.cell_value(nrow-1,3)
      pres=sheet.cell_value(nrow-1,4)
      humidity=sheet.cell_value(nrow-1,5)
      windspeed=sheet.cell_value(nrow-1,6)
      desc=sheet.cell_value(nrow-1,7)
      sunrise=sheet.cell_value(nrow-1,8)
      sunset=sheet.cell_value(nrow-1,9)
      curr_time=sheet.cell_value(nrow-1,0)
      #========================================================================Location=================================================
      dataframe=pd.read_excel('https://s3.console.aws.amazon.com/s3/buckets/zappa-q8s9hsqwq/spreadsheets/' + checked_files[-1])
      locations = dataframe[['Latitude', 'Longitude']]
      locationlist = locations.values.tolist()
      map = folium.Map(location=locationlist[0], zoom_start=12,tiles='openstreetmap')
      for point in range(0, len(locationlist)):
          folium.Marker(locationlist[point], color='#3186cc',fill=True,fill_color='#3186cc').add_to(map)
      #folium.Marker(location=[lat,lon],radius=50,color='#3186cc',fill=True,fill_color='#3186cc').add_to(m)
      map.save("./templates/location.html")
      geolocator = Nominatim(user_agent="my-application")
      location = geolocator.reverse(""+str(lat)+","+str(lon)+"")
      print(location.address)

      return render_template('ResultsWeb.html',curr_time=curr_time,temp=temp, pres=pres, humidity=humidity,ws=windspeed, desc=desc,location=location.address,sunrise=sunrise,sunset=sunset)

@application.route('/blog', methods=['GET','POST'])
def blog():
    if request.method == 'GET':
        return render_template('blog.html')

@application.route('/map', methods=['GET','POST'])
@login_required
def map():
    if request.method == 'GET':
        return render_template('location.html')

@application.route('/technology', methods=['GET','POST'])
@login_required
def technology():
    if request.method == 'GET':
        event_post = []
        event_train = []
        event_date = []
        event_title = []
        training_df = pd.DataFrame()
        chrome_path = r"C:\Users\akadam\Desktop\chromedriver.exe"
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('headless')
        driver = webdriver.Chrome(chrome_path, options=chrome_options)
        #driver  =  webdriver.Chrome(chrome_path)
        driver.get("https://automotivedigest.com/events/")
        posts = driver.find_elements_by_class_name("person")
        event_post.clear()
        for post in posts:
            event_post.append(post.text)
        driver.close()

        browser =  webdriver.Chrome(chrome_path, options=chrome_options)
        browser.get("https://www.automotiveworld.com/webinars/")
        trainings = browser.find_elements_by_class_name("posts-items")
        date = browser.find_elements_by_class_name("day-month")
        title = browser.find_elements_by_class_name("post-title")
        #time.sleep(1)
        
        event_train.clear()
        for train in trainings:
            event_train.append(train.text)
        for dates in date:
            event_date.append(dates.text)
        for titles in title:
            event_title.append(titles.text)
        training_df['Date'] = event_date
        training_df['Title'] = event_title
        browser.close()
        return render_template('technology.html', posts= event_post, trainings = event_train, tables=[training_df.to_html(classes='data', header="true")])
        

@application.route('/translation', methods=['GET','POST'])
def translation():
    if request.method == 'GET':
        return render_template('translation.html')


@application.route('/translate', methods=['GET', 'POST'])
def translate():
    translator = Translator()
    if request.method == 'POST':
        file = request.files['translate_file']
        content = file.read()
        content = content.decode('utf-16')
        file.save(secure_filename(file.filename))
        lang = request.form.get('language')
        file1 = open("./translated_doc/file.txt","w", encoding = "utf-8")
        if lang == "English":
            result = translator.translate(content, dest='en')
        elif lang == "Chinese":
            result = translator.translate(content, dest='zh-cn')
        elif lang == "Japanese":
            result = translator.translate(content, dest='ja')
        elif lang == "German":
            result = translator.translate(content, dest='de')
        elif lang == "Hindi":
            result = translator.translate(content, dest='hi')
        file1.writelines(result.text)
        print(file1)

        return render_template('translation.html', lang= str(lang))
    else:
        return render_template('translation.html')

@application.route('/analysis', methods = ['GET', 'POST'])
def analysis():
    if request.method == 'GET':
        return render_template('analysis.html')

@application.route('/analyze', methods=['GET','POST'])
def analyze():
    if request.method == 'POST':
        file = request.files['analysis_file']
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket='isuzu-sagemaker',
            Key='input/analysis.csv',
            Body=file
        )
        methods = request.form.get('method')
        models = request.form.get('model')
        if models == "train":
            if methods == "linearReg":
                ls3 = boto3.resource('s3')
                my_pickle = pickle.loads(ls3.Bucket('isuzu-sagemaker').Object("linear-regression/output.pkl").get()['Body'].read())
                #runpy.run_module(mod_name='trial_visualization')
                #images = os.listdir(os.path.join('./static/', "SensorsPlots"))


                #images = os.listdir(os.path.join('https://zappa-q8s9hsqwq.s3.amazonaws.com/static/', "SensorsPlots"))

                return render_template('analysis.html', loss=my_pickle)
        else:
            return render_template('analysis.html')



#----------------------------------------------------visualization-------------------------------------------------------------------

@application.route('/portfolio')
def portfolio():
    runpy.run_module(mod_name='trial_visualization')
    images = os.listdir(os.path.join('./static/', "SensorsPlots"))
    return render_template('trial_visualize.html', images=images)

if __name__ == '__main__':
   application.run()