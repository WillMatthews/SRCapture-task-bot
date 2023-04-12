from selenium import webdriver
from time import sleep
import re
import subprocess
from datetime import datetime


# if I were to redo this, I'd have a page which dynamically updates with AJAX.
# This was made in approx half an hour to enable supervisors to quickly see what is going on


# This bot iterates over all questions on a SRCapture marking page, highlighting
# how many papers are left to mark. This is then compiled into a static html file, and uploaded to
# server where the results can be seen.
# This functionality does not exist in SRCapture, so it might help with users
# trying to organise a hoarde of markers.
# no warranty, no license, software taken as is. Enjoy :)

url_login = "https://cloud2.srcapture.com/src/Login#/"
url_check = "https://cloud2.srcapture.com/src/App#/usertask/list/"
mainpage  = "https://cloud2.srcapture.com/src/App#/"

# page ids can be identified by hovering over the links for each question.
# These ids are continuous and sequential, therefore we just need to know the first
# and the last question being marked for us to iterate over and check how many are remaining.
# the name must have no spaces. hyphens and underscores are allowed.
papers    = [{'name':'Physics', 'page_ids':[i for i in range(21,35)]}, {'name':'Engineering', 'page_ids':[i for i in range(10,12)]}]

# SRCapture login credentials
username  = "replace_with_user_name"
password  = "replace_with_password"

# Your Server's login for scp of generated html files
server_dest = "username@server:path"

headers   = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


# A stylesheet can be included. None is provided here as this is a bare minimum example.
# to include a stylesheet, do the following, but replace the href with your link of course
# <link rel="stylesheet" href="/css/style.css">

top = """
<!-- if you're reading this - there's nothing of interest here. This is just the output of a static site generator. Yes - I am aware the html is awful, but I made this in 10 mins so no complaining. -->
<!DOCTYPE html>
<head>
<meta http-equiv="refresh" content="15">
<style>
body {
  font-family: arial, sans-serif;
}
table {
  border-collapse: collapse;
  width: 100%;
}
td, th {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}
tr:nth-child(even) {
background-color: #dddddd;
}
tr:hover {background-color: yellow;}
#myProgress {
  width: 100%;
  background-color: #ddd;
  overflow :hidden;
}
#myBar {
  width: 0%;
  height: 30px;
  background-color: #04AA6D;
  text-align: center;
  line-height: 30px;
  color: white;
  overflow :hidden;
}
</style>

<style>

</style>
tr:nth-child(even) {
background-color: #073642;
}
tr:hover {background-color: blue;}
</style>

<title>SRCapture Dashboard</title>

</head>
<body>

<h1> SRCapture Scrape title_dummy </h1>
<h3> Page Automatically Refreshes Every 15 Seconds </h3>

<div id="myProgress">
  <div id="myBar"></div>
</div>

<script>
  var i = 0;
  if (i == 0) {
    i = 1;
    var elem = document.getElementById("myBar");
    var wid = document.getElementById("wid");
    var width = 0;
    var id = setInterval(frame, 10);
    var tleft = 15;
    var sec_left = 15;
    function frame() {
      if (width >= 100) {
        clearInterval(id);
        i = 0;
      } else {
        width = width + 1/15;
        elem.style.width = width + "%";

        sec_left = (15-width*15/100);
        tleft = Math.round( sec_left * 10) / 10;
        elem.innerHTML = sec_left.toFixed(1) + " Seconds";
      }
    }
  }

</script>

<table>
    <tr>
    <th>Task Name</th>
    <th>Task Count</th>
    <th>Available Task Count</th>
    <th>Checked at</th>
  </tr>

"""

bottom = "</table></body></html>"

butmatch = "<\s*button[^>]*>(.*?)<\s*/\s*button>"

# HTML to replace on the web form so we only get the data that we need
replace_text_srcapture = """<thead><tr><th class="clickableHeader">Task Name<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 10 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M7 7V3H3v4H0l5 6 5-6H7z"></path></svg></th><th class="clickableHeader">Task Count</th><th class="clickableHeader">Available Task Count</th><th>Process</th><th class="clickableHeader">My Tasks</th></tr></thead><tbody><tr>"""

# Use Selenium to create a firefox window. wget/curl does NOT work with SRCapture so we have to do this.
driver = webdriver.Firefox()

# login to srcapture
driver.get(url_login)
sleep(1)
driver.find_element_by_name('Username').send_keys(username)
driver.find_element_by_name('Password').send_keys(password)
driver.find_element_by_class_name("btn").click()
sleep(2)


# Repeat Forever... This could be changed to something on the order of 'if all tasks are zero'
while True:
    for group in papers:
        outpage_name = 'output_' + group['name'] + '.html'
        open(outpage_name, 'w').close()
        with open(outpage_name, "a") as f:
            f.write(re.sub("title_dummy", group['name'], top))
            for ident in group['page_ids']:
                driver.get(mainpage)
                sleep(0.65)
                newurl = url_check+str(ident)
                print("\nGetting", newurl)
                driver.get(newurl)
                sleep(0.25)
                noTbl = True
                while noTbl:
                    try:
                        eltable   = driver.find_element_by_class_name("table")
                        tabledata = eltable.get_attribute('innerHTML')
                        tabledata = re.sub(replace_text_srcapture, "", tabledata)
                        tabledata = re.sub(butmatch, "", tabledata)
                        tabledata = re.sub("</td><td><span></span></td>", "", tabledata)
                        tabledata = re.sub("<tbody>", "", tabledata)
                        tabledata = re.sub("</tbody>", "", tabledata)
                        tabledata = re.sub("<td></tr>", "</tr>", tabledata)
                        tabledata = re.sub("<td></td><td></td>", "", tabledata)
                        now = datetime.now()
                        tabledata = re.sub("</tr>", "<td>" + now.strftime("%H:%M:%S") + "</td></tr>", tabledata)
                        f.write(tabledata)
                        print(tabledata)
                        noTbl = False
                    except Exception:
                        sleep(0.4)
            f.write(bottom)

        subprocess.Popen(["scp", outpage_name, server_dest])

driver.quit()
