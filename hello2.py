import cgi
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import misc_var as page
import sys
import datetime
import pytz

def nav_index(n,tot,start):
	if n+start>=tot:
		old=-1
	else :
		old=n+start
	
	if n-5<0:
		new=-1
	else :
		new=n-5

	return old,new

class News(db.Model):
	author = db.StringProperty()
	title=db.StringProperty()
	date=db.StringProperty()
	content = db.TextProperty()	#(multiline=True)
	submission_date = db.DateTimeProperty()
	is_modified=db.BooleanProperty()

class PageStat(db.Model):
	Lastmodified=db.StringProperty()

class MainPage(webapp.RequestHandler):
	def get(self):
		self.response.out.write(page.start)
		if users.get_current_user()!=None:
			self.response.out.write("hello, <b>%s</b>"%users.get_current_user())
		else :
			self.response.out.write("""<form action="/login" method="post"><input type="submit" value="login" style="background:none;border:0;color:#ff0000"></form>""")
		
		if self.request.get('num'):		# to determine which objects to fetch
			n=int(self.request.get('num'))  # from the datastore
		else :
			n=0
		
		start=0
	
		c=db.GqlQuery("SELECT * FROM News ORDER BY submission_date DESC").count()
		# modified the query to fetch only the objects needed
		posts = db.GqlQuery("SELECT * FROM News ORDER BY submission_date DESC LIMIT %d,%d"%(n,5))
		
		for entry in posts:
			self.response.out.write('''<div id="news">''')
			self.response.out.write("<b>%s</b><br>" % entry.title)
			self.response.out.write("<i>%s</i>:&nbsp;%s<br>" % (cgi.escape(entry.date),entry.content))
		
			if str(users.get_current_user())==entry.author:
				self.response.out.write('''<a href="/edit?toedit=%d">Edit</a>'''%(n+start))

			if not entry.is_modified:
				self.response.out.write("<div id=post_detail>Posted by %s at %s UTC</div>"%(entry.author,entry.submission_date))
			else :
				self.response.out.write("<div id=post_detail>Last modified by %s at %s UTC</div>"%(entry.author,entry.submission_date))

			self.response.out.write('''</div>\n''')
			start+=1
		
		
		if n+start<c and n-5>=0:
			self.response.out.write('''<div id=nav>
				<h5><a href="/news?num=%d">&lt;&lt;Older</a>&nbsp;&nbsp;<a href="/news?num=%d">Newer&gt;&gt;</a></h5></div>
	'''%(n+start,n-5))
		elif n+start>=c and n-5>=0:
			self.response.out.write('''<div id=nav>
				<h5>&lt;&lt;Older&nbsp;&nbsp;<a href="/news?num=%d">Newer&gt;&gt;</a></h5></div>
										        '''%(n-5))
		elif n+start<c and n-5<0:
			self.response.out.write('''<div id=nav>
                                <h5><a href="/news?num=%d">&lt;&lt;Older</a>&nbsp;&nbsp;Newer&gt;&gt;</h5></div>
        '''%(n+start))
		else :
			self.response.out.write('''<div id=nav>
                                <h5>&lt;&lt;Older&nbsp;&nbsp;Newer&gt;&gt;</h5></div>
										        ''')



		# Write the submission form and the footer of the page
		if page.valid_ids.count(str(users.get_current_user()).strip())!=0:
			self.response.out.write("""
			<h3>Add new entry:</h3>
              		<form action="/sign" method="post">
			<input type="text" name="title" value="Enter the title:">
			<input type="text" name="date" value="Enter the date of the event:">
                	<div><textarea name="content" rows="3" cols="60"></textarea></div>
                	<div><input type="submit" value="Post"></div>
              		</form>
           		</body>
          		</html>""")

#		else :
#			self.redirect(users.create_login_url(self.request.uri))
		
		lastmod=db.GqlQuery("SELECT * FROM PageStat LIMIT 0,1")[0].Lastmodified
	
		self.response.out.write(page.foot%lastmod)


class UpdateNews(webapp.RequestHandler):
	def post(self):
		if page.valid_ids.count(str(users.get_current_user()).strip())!=0:

			if not self.request.get('toedit'):
				entry = News()
				entry.author = (str(users.get_current_user())).strip()
				entry.content = self.request.get('content')
				entry.date = self.request.get('date')
				entry.title = self.request.get('title')
				entry.submission_date=datetime.datetime.now()
				entry.put()
				self.redirect('/news')
				
				stat=db.GqlQuery("SELECT * FROM PageStat LIMIT 0,1")[0]
				stat.Lastmodified=str(datetime.datetime.now())
				stat.put()

	
			
			else :
				num=int(self.request.get('toedit'))
				posts = db.GqlQuery("SELECT * FROM News ORDER BY submission_date DESC LIMIT %d,%d"%(num,2))
		
				entry=posts[num]
				entry.author = (str(users.get_current_user())).strip()
				entry.content = self.request.get('content')
				entry.date = self.request.get('date')
				entry.title = self.request.get('title')
				entry.is_modified = True
				entry.submission_date=datetime.datetime.now()
				entry.put()
				self.redirect('/news')
				
				stat=db.GqlQuery("SELECT * FROM PageStat LIMIT 0,1")[0]
				stat.Lastmodified=str(datetime.datetime.now())
				stat.put()


		else :
			self.redirect(users.create_login_url(self.request.uri))


class Edit(webapp.RequestHandler):
	def get(self):
		if (str(users.get_current_user())).strip():
			if page.valid_ids.count(str(users.get_current_user()).strip())!=0:
				num=int(self.request.get('toedit'))
				posts = db.GqlQuery("SELECT * FROM News ORDER BY submission_date DESC LIMIT %d,%d"%(num,2))
				entry=posts[num]
				self.response.out.write(page.start)	
				self.response.out.write("""<h3>Edit this post</h3><br>""")
	                        self.response.out.write("""
	                        <form action="/sign?toedit=%d" method="post">
	                        <input type="text" name="title" value="%s">
	                        <input type="text" name="date" value="%s">
	                        <div><textarea name="content" rows="3" cols="60">%s</textarea></div>
	                        <div><input type="submit" value="Post"></div>
	                        </form>
	                        </body>
			        </html>"""%(num,cgi.escape(entry.title),cgi.escape(entry.date),entry.content))
			
				lastmod=db.GqlQuery("SELECT * FROM PageStat")[0].Lastmodified

				self.response.out.write(page.foot%lastmod)


			else :
				self.response.out.write(page.start)
				self.response.out.write("""<h4>You are not authorized to edit this post</h4>""")
			
				lastmod=db.GqlQuery("SELECT * FROM PageStat")[0].Lastmodified

				self.response.out.write(page.foot%lastmod)

                else :
			self.redirect(users.create_login_url(self.request.uri))

class Login(webapp.RequestHandler):
#	def get(self):
#		self.redirect(users.create_login_url(MainPage))
	def post(self):
		self.redirect(users.create_login_url('http://astro.iiserk.net/news'))


application = webapp.WSGIApplication([('/news', MainPage),('/login',Login),('/sign', UpdateNews),('/edit', Edit)],debug=True)


def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()

