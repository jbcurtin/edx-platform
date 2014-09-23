"""
This config file runs the simplest dev environment using sqlite, and db-based
sessions. Assumes structure:

/envroot/
        /db   # This is where it'll write the database file
        /edx-platform  # The location of this repo
        /log  # Where we're going to write log files
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=W0401, W0614

from .common import *
import os
from path import path
from warnings import filterwarnings, simplefilter
from uuid import uuid4

# mongo connection settings
MONGO_PORT_NUM = int(os.environ.get('EDXAPP_TEST_MONGO_PORT', '27017'))
MONGO_HOST = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'localhost')

os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000-9000'

THIS_UUID = uuid4().hex[:5]

# can't test start dates with this True, but on the other hand,
# can test everything else :)
FEATURES['DISABLE_START_DATES'] = True

# Most tests don't use the discussion service, so we turn it off to speed them up.
# Tests that do can enable this flag, but must use the UrlResetMixin class to force urls.py
# to reload. For consistency in user-experience, keep the value of this setting in sync with
# the one in cms/envs/test.py
FEATURES['ENABLE_DISCUSSION_SERVICE'] = False

FEATURES['ENABLE_SERVICE_STATUS'] = True

FEATURES['ENABLE_HINTER_INSTRUCTOR_VIEW'] = True

FEATURES['ENABLE_INSTRUCTOR_LEGACY_DASHBOARD'] = True

FEATURES['ENABLE_SHOPPING_CART'] = True

FEATURES['ENABLE_VERIFIED_CERTIFICATES'] = True

# Enable this feature for course staff grade downloads, to enable acceptance tests
FEATURES['ENABLE_S3_GRADE_DOWNLOADS'] = True
FEATURES['ALLOW_COURSE_STAFF_GRADE_DOWNLOADS'] = True

# Toggles embargo on for testing
FEATURES['EMBARGO'] = True

# Need wiki for courseware views to work. TODO (vshnayder): shouldn't need it.
WIKI_ENABLED = True

# Makes the tests run much faster...
SOUTH_TESTS_MIGRATE = False  # To disable migrations and use syncdb instead

# Nose Test Runner
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

_system = 'lms'

_report_dir = REPO_ROOT / 'reports' / _system
_report_dir.makedirs_p()

NOSE_ARGS = [
    '--id-file', REPO_ROOT / '.testids' / _system / 'noseids',
    '--xunit-file', _report_dir / 'nosetests.xml',
]

# Local Directories
TEST_ROOT = path("test_root")
# Want static files in the same dir for running on jenkins.
STATIC_ROOT = TEST_ROOT / "staticfiles"

STATUS_MESSAGE_PATH = TEST_ROOT / "status_message.json"

COURSES_ROOT = TEST_ROOT / "data"
DATA_DIR = COURSES_ROOT

COMMON_TEST_DATA_ROOT = COMMON_ROOT / "test" / "data"
# Where the content data is checked out.  This may not exist on jenkins.
GITHUB_REPO_ROOT = ENV_ROOT / "data"

USE_I18N = True
LANGUAGE_CODE = 'en'  # tests assume they will get English.

XQUEUE_INTERFACE = {
    "url": "http://sandbox-xqueue.edx.org",
    "django_auth": {
        "username": "lms",
        "password": "***REMOVED***"
    },
    "basic_auth": ('anant', 'agarwal'),
}
XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds

# Don't rely on a real staff grading backend
MOCK_STAFF_GRADING = True
MOCK_PEER_GRADING = True

# TODO (cpennington): We need to figure out how envs/test.py can inject things
# into common.py so that we don't have to repeat this sort of thing
STATICFILES_DIRS = [
    COMMON_ROOT / "static",
    PROJECT_ROOT / "static",
]
STATICFILES_DIRS += [
    (course_dir, COMMON_TEST_DATA_ROOT / course_dir)
    for course_dir in os.listdir(COMMON_TEST_DATA_ROOT)
    if os.path.isdir(COMMON_TEST_DATA_ROOT / course_dir)
]

# Avoid having to run collectstatic before the unit test suite
# If we don't add these settings, then Django templates that can't
# find pipelined assets will raise a ValueError.
# http://stackoverflow.com/questions/12816941/unit-testing-with-django-pipeline
STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage'
PIPELINE_ENABLED=False

update_module_store_settings(
    MODULESTORE,
    module_store_options={
        'fs_root': TEST_ROOT / "data",
    },
    xml_store_options={
        'data_dir': COMMON_TEST_DATA_ROOT,
    },
    doc_store_settings={
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'db': 'test_xmodule',
        'collection': 'test_modulestore{0}'.format(THIS_UUID),
    },
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'db': 'xcontent',
        'port': MONGO_PORT_NUM,
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_ROOT / 'db' / 'edx.db'
    },

}

CACHES = {
    # This is the cache used for most things.
    # In staging/prod envs, the sessions also live here.
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_loc_mem_cache',
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    # The general cache is what you get if you use our util.cache. It's used for
    # things like caching the course.xml file for different A/B test groups.
    # We set it to be a DummyCache to force reloading of course.xml in dev.
    # In staging environments, we would grab VERSION from data uploaded by the
    # push process.
    'general': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'KEY_PREFIX': 'general',
        'VERSION': 4,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },

    'mongo_metadata_inheritance': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '/var/tmp/mongo_metadata_inheritance',
        'TIMEOUT': 300,
        'KEY_FUNCTION': 'util.memcache.safe_key',
    },
    'loc_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edx_location_mem_cache',
    },

}

# Dummy secret key for dev
SECRET_KEY = '85920908f28904ed733fe576320db18cabd7b6cd'

# hide ratelimit warnings while running tests
filterwarnings('ignore', message='No request passed to the backend, unable to rate-limit')

# Ignore deprecation warnings (so we don't clutter Jenkins builds/production)
# https://docs.python.org/2/library/warnings.html#the-warnings-filter
simplefilter('ignore')  # Change to "default" to see the first instance of each hit
                        # or "error" to convert all into errors

######### Third-party auth ##########
FEATURES['ENABLE_THIRD_PARTY_AUTH'] = True

################################## OPENID #####################################
FEATURES['AUTH_USE_OPENID'] = True
FEATURES['AUTH_USE_OPENID_PROVIDER'] = True

################################## SHIB #######################################
FEATURES['AUTH_USE_SHIB'] = True
FEATURES['SHIB_DISABLE_TOS'] = True
FEATURES['RESTRICT_ENROLL_BY_REG_METHOD'] = True

OPENID_CREATE_USERS = False
OPENID_UPDATE_DETAILS_FROM_SREG = True
OPENID_USE_AS_ADMIN_LOGIN = False
OPENID_PROVIDER_TRUSTED_ROOTS = ['*']

############################## OAUTH2 Provider ################################
FEATURES['ENABLE_OAUTH2_PROVIDER'] = True

###################### Payment ##############################3
# Enable fake payment processing page
FEATURES['ENABLE_PAYMENT_FAKE'] = True

# Configure the payment processor to use the fake processing page
# Since both the fake payment page and the shoppingcart app are using
# the same settings, we can generate this randomly and guarantee
# that they are using the same secret.
from random import choice
import string
RANDOM_SHARED_SECRET = ''.join(
    choice(string.letters + string.digits + string.punctuation)
    for x in range(250)
)

CC_PROCESSOR_NAME = 'CyberSource2'
CC_PROCESSOR['CyberSource2']['SECRET_KEY'] = RANDOM_SHARED_SECRET
CC_PROCESSOR['CyberSource2']['ACCESS_KEY'] = "0123456789012345678901"
CC_PROCESSOR['CyberSource2']['PROFILE_ID'] = "edx"
CC_PROCESSOR['CyberSource2']['PURCHASE_ENDPOINT'] = "/shoppingcart/payment_fake"

FEATURES['STORE_BILLING_INFO'] = True

########################### SYSADMIN DASHBOARD ################################
FEATURES['ENABLE_SYSADMIN_DASHBOARD'] = True
GIT_REPO_DIR = TEST_ROOT / "course_repos"

################################# CELERY ######################################

CELERY_ALWAYS_EAGER = True
CELERY_RESULT_BACKEND = 'cache'
BROKER_TRANSPORT = 'memory'

############################ STATIC FILES #############################
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = TEST_ROOT / "uploads"
MEDIA_URL = "/static/uploads/"
STATICFILES_DIRS.append(("uploads", MEDIA_ROOT))

new_staticfiles_dirs = []
# Strip out any static files that aren't in the repository root
# so that the tests can run with only the edx-platform directory checked out
for static_dir in STATICFILES_DIRS:
    # Handle both tuples and non-tuple directory definitions
    try:
        _, data_dir = static_dir
    except ValueError:
        data_dir = static_dir

    if data_dir.startswith(REPO_ROOT):
        new_staticfiles_dirs.append(static_dir)
STATICFILES_DIRS = new_staticfiles_dirs

FILE_UPLOAD_TEMP_DIR = TEST_ROOT / "uploads"
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

########################### Server Ports ###################################

# These ports are carefully chosen so that if the browser needs to
# access them, they will be available through the SauceLabs SSH tunnel
LETTUCE_SERVER_PORT = 8003
XQUEUE_PORT = 8040
YOUTUBE_PORT = 8031
LTI_PORT = 8765
VIDEO_SOURCE_PORT = 8777

################### Make tests faster

#http://slacy.com/blog/2012/04/make-your-tests-faster-in-django-1-4/
PASSWORD_HASHERS = (
    # 'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    # 'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    # 'django.contrib.auth.hashers.CryptPasswordHasher',
)

### This enables the Metrics tab for the Instructor dashboard ###########
FEATURES['CLASS_DASHBOARD'] = True

################### Make tests quieter

# OpenID spews messages like this to stderr, we don't need to see them:
#   Generated checkid_setup request to http://testserver/openid/provider/login/ with assocication {HMAC-SHA1}{51d49995}{s/kRmA==}

import openid.oidutil
openid.oidutil.log = lambda message, level = 0: None

PLATFORM_NAME = "edX"
SITE_NAME = "edx.org"

# set up some testing for microsites
MICROSITE_CONFIGURATION = {
    "test_microsite": {
        "domain_prefix": "testmicrosite",
        "university": "test_microsite",
        "platform_name": "Test Microsite",
        "logo_image_url": "test_microsite/images/header-logo.png",
        "email_from_address": "test_microsite@edx.org",
        "payment_support_email": "test_microsite@edx.org",
        "ENABLE_MKTG_SITE": False,
        "SITE_NAME": "test_microsite.localhost",
        "course_org_filter": "TestMicrositeX",
        "course_about_show_social_links": False,
        "css_overrides_file": "test_microsite/css/test_microsite.css",
        "show_partners": False,
        "show_homepage_promo_video": False,
        "course_index_overlay_text": "This is a Test Microsite Overlay Text.",
        "course_index_overlay_logo_file": "test_microsite/images/header-logo.png",
        "homepage_overlay_html": "<h1>This is a Test Microsite Overlay HTML</h1>",
        "ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER": False,
    },
    "default": {
        "university": "default_university",
        "domain_prefix": "www",
    }
}
MICROSITE_ROOT_DIR = COMMON_ROOT / 'test' / 'test_microsites'
MICROSITE_TEST_HOSTNAME = 'testmicrosite.testserver'

FEATURES['USE_MICROSITES'] = True

# add extra template directory for test-only templates
MAKO_TEMPLATES['main'].extend([
    COMMON_ROOT / 'test' / 'templates'
])


######### LinkedIn ########
LINKEDIN_API['COMPANY_ID'] = '0000000'

# Setting for the testing of Software Secure Result Callback
VERIFY_STUDENT["SOFTWARE_SECURE"] = {
        "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
        "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
}

VIDEO_CDN_URL = {
    'CN': 'http://api.xuetangx.com/edx/video?s3_url='
}

######### dashboard git log settings #########
MONGODB_LOG = {
    'host': MONGO_HOST,
    'port': MONGO_PORT_NUM,
    'user': '',
    'password': '',
    'db': 'xlog',
}
