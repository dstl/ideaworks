(c) Crown Copyright 2014 Defence Science and Technology Laboratory UK
Author: Rich Brantingham

#Dependency Licenses

| Library                             | License       | Link																													|
|-------------------------------------|---------------|-------------------------------------------------------------------------------------------------------------------------|
| Django==1.5.1						  | BSD           | https://github.com/django/django/blob/master/LICENSE 																	|
| PyYAML==3.10						  | MIT           | http://pyyaml.org/wiki/PyYAML																					 		|
| biplist==0.6						  | BSD (pypi)    | https://github.com/wooster/biplist/blob/master/LICENSE																    |
| defusedxml==0.4.1					  | PSF			  | https://bitbucket.org/tiran/defusedxml/src/ac560aaf6f4a8c1e00b7961a11123d7580110056/LICENSE?at=default					|
| django-profiles==0.2				  | BSD-based     | https://github.com/tualatrix/django-profile/blob/master/LICENSE.txt														|
| django-registration==1.0			  | BSD-based     | https://bitbucket.org/ubernostrum/django-registration/src/8f242e35ef7c004e035e54b4bb093c32bf77c29f/LICENSE?at=default	|
| django-registration-email==0.7.1	  | Unlicense     | https://github.com/bitmazk/django-registration-email/blob/master/LICENSE												|
| django-tastypie==0.11.1-dev		  | BSD 		  | https://github.com/toastdriven/django-tastypie/blob/master/LICENSE														|
| django-tastypie-mongoengine==0.4.5  | AGPL		  | https://github.com/wlanslovenija/django-tastypie-mongoengine/blob/master/LICENSE										|
| django-tastytools==0.1.0			  | BSD-based	  | https://github.com/juanique/django-tastytools/blob/master/LICENSE														|
| docutils==0.11					  | Public Domain | http://docutils.sourceforge.net/COPYING.html																			|
| lxml==3.3.2						  | BSD			  | http://lxml.de/																					 						|
| mongoengine==0.8.7				  | MIT			  | https://github.com/MongoEngine/mongoengine/blob/master/LICENSE															|
| nose==1.3.0						  | LGPL		  | https://github.com/nose-devs/nose/blob/master/lgpl.txt																	|
| pymongo==2.6.3					  | Apache		  | https://github.com/mongodb/mongo-python-driver/blob/master/LICENSE														|
| python-dateutil==2.2				  | BSD			  | https://pypi.python.org/pypi/python-dateutil																			|
| python-mimeparse==0.1.4			  | MIT			  | https://code.google.com/p/mimeparse/																					|
| requests==2.2.1					  | Apache		  | https://github.com/kennethreitz/requests/blob/master/LICENSE															|
| six==1.5.2						  | MIT			  | https://pypi.python.org/pypi/six																					    |
| wsgiref==0.1.2					  | PSF or ZPL    | https://pypi.python.org/pypi/wsgiref																					|
| JQuery                              | MIT           | https://jquery.org/license                                                                                               | 
| jQuery Cookie                       | MIT           | https://github.com/carhartl/jquery-cookie/blob/master/MIT-LICENSE.txt                                                    |
| Bootstrap                           | Apache        | http://www.apache.org/licenses/LICENSE-2.0                                                                               |
| Bootstrap Sortable                  | Github OS     | https://github.com/drvic10k/bootstrap-sortable/blob/master/license.md                                                    |
| Bootstrap Select                    | MIT           | https://github.com/caseyjhol/bootstrap-select                                                                            |
| Respond.js                          | MIT           | https://github.com/scottjehl/Respond/blob/master/LICENSE-MIT                                                             |
| Html5shiv.js                        | MIT           | https://code.google.com/p/html5shiv/                                                                                     |
| AngularJS                           | MIT           | https://github.com/angular/angular.js/blob/master/LICENSE                                                                |
| Angular UI Bootstrap                | MIT           | https://github.com/angular-ui/bootstrap/blob/master/LICENSE                                                              |
| Angular Bootstrap Select            | MIT           | https://github.com/joaoneto/angular-bootstrap-select                                                                     |
| Angular ng-grid                     | MIT           | https://github.com/angular-ui/ng-grid/blob/master/LICENSE.md                                                             |
| textAngular                         | MIT           | https://github.com/fraywing/textAngular/                                                                                 |
| Font awesome                        | SIF OFL 1.1   | http://fontawesome.io/license/                                                                                           |


* BSD, MIT, PSF and Apache all OK.

* LGPL (Nose) code is OK as a dependency because it is being handled independently from the Dstl code.
  Nose is only used in the testing framework so doesn't necessarily have to be distributed with the code - although clearly bad form.

* AGPL code (Django-tastypie-mongoengine)
  http://stackoverflow.com/questions/6500925/agpl-license-question-re-neo4j/7505274#7505274
  
  AGPL correctly dealt with by licensing under AGPL.
  
  