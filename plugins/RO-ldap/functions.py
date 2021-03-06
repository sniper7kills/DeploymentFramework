import crypt
import string
try:  # 3.6 or above
    from secrets import choice as randchoice
except ImportError:
    from random import SystemRandom
    randchoice = SystemRandom().choice

def sha512_crypt(password, salt=None, rounds=None):
    if salt is None:
        salt = ''.join([randchoice(string.ascii_letters + string.digits)
                        for _ in range(8)])
    prefix = '$6$'
    if rounds is not None:
        rounds = max(1000, min(999999999, rounds or 5000))
        prefix += 'rounds={0}$'.format(rounds)
    return crypt.crypt(password, prefix + salt)

def dockerFile(domain):
    return """
  ldap:
    image: tiredofit/openldap:latest
    restart: unless-stopped
    hostname: ldap.%s
    volumes:
      - ./storage/ldap/data:/var/lib/openldap
      - ./storage/ldap/config:/etc/openldap/slapd.d
      - ./init/ldap/ldifs:/assets/S7K-LDIF
      - ./storage/ldap/certs:/certs
      - ./storage/ldap/backup:/data/backup
    env_file:
      - ./envs/ldap.env
""" % domain

def envFile(domain, organization, admin_pass, config_pass, s3_bucket):
    return """DOMAIN=%s
ORGANIZATION=%s

ADMIN_PASS=%s
CONFIG_PASS=%s

ENABLE_READONLY_USER=FALSE
READONLY_USER_USER=reader
READONLY_USER_PASS=reader

HOSTNAME=ldap.%s
LOG_LEVEL=256

SCHEMA_TYPE=nis

DEBUG_MODE=FALSE

ENABLE_TLS=TRUE
TLS_CREATE_CA=TRUE
TLS_CRT_FILENAME=cert.pem
TLS_KEY_FILENAME=key.pem
TLS_ENFORCE=FALSE
TLS_CIPHER_SUITE=ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:-DHE-DSS:-RSA:!aNULL:!MD5:!DSS:!SHA
TLS_VERIFY_CLIENT=never
SSL_HELPER_PREFIX=ldap

REMOVE_CONFIG_AFTER_SETUP=true

ENABLE_BACKUP=TRUE
BACKUP_S3_BUCKET=%s
BACKUP_INTERVAL=0400
BACKUP_RETENTION=10080

CONTAINER_ENABLE_MONITORING=TRUE
CONTAINER_NAME=ldap
""" % (domain, organization, admin_pass, config_pass, domain, s3_bucket)

def serviceAccountLDIF(base_dn, username, password):
      return """
dn: cn=%s,ou=Service,ou=Accounts,%s
cn: %s
objectClass: simpleSecurityObject
objectClass: organizationalRole
userpassword: {CRYPT}%s

dn: cn=Services,ou=Security,ou=Groups,%s
changetype: modify
add: member
member: cn=%s,ou=Service,ou=Accounts,%s
""" % (username, base_dn, username, sha512_crypt(password), base_dn, username, base_dn)

def guacamoleSchema():
      return """dn: cn=guacConfigGroup,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: guacConfigGroup
olcAttributeTypes: {0}( 1.3.6.1.4.1.38971.1.1.1 NAME 'guacConfigProtocol' SYNTAX 1.3.6.1.4.1.1466
 .115.121.1.15 )
olcAttributeTypes: {1}( 1.3.6.1.4.1.38971.1.1.2 NAME 'guacConfigParameter' SYNTAX 1.3.6.1.4.1.146
 6.115.121.1.15 )
olcObjectClasses: {0}( 1.3.6.1.4.1.38971.1.2.1 NAME 'guacConfigGroup' DESC 'Guacamole configuration group' SUP groupOfNames MUST guacConfigProtocol MAY guacConfigParameter )"""

def postfixSchema():
  return """
dn: cn=postfix,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: postfix
# $Id$
#
# State of Mind
# Private Enterprise Number: 29426
#
# OID prefix: 1.3.6.1.4.1.29426
#
# Attributes: 1.3.6.1.4.1.29426.1.10.x
#
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.1 NAME 'mailHomeDirectory'
  DESC 'The absolute path to the mail user home directory'
  EQUALITY caseExactIA5Match
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.2 NAME 'mailAlias'
  DESC 'RFC822 Mailbox - mail alias'
  EQUALITY caseIgnoreIA5Match
  SUBSTR caseIgnoreIA5SubstringsMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26{256} )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.3 NAME 'mailUidNumber'
  DESC 'UID required to access the mailbox'
  EQUALITY integerMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.4 NAME 'mailGidNumber'
  DESC 'GID required to access the mailbox'
  EQUALITY integerMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.5 NAME 'mailEnabled'
  DESC 'TRUE to enable, FALSE to disable account'
  EQUALITY booleanMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.7 SINGLE-VALUE )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.6 NAME 'mailGroupMember'
  DESC 'Name of a mail distribution list'
  EQUALITY caseExactIA5Match
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.7 NAME 'mailQuota'
  DESC 'Mail quota limit in kilobytes'
  EQUALITY caseExactIA5Match
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.8 NAME 'mailStorageDirectory'
  DESC 'The absolute path to the mail users mailbox'
  EQUALITY caseExactIA5Match
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26 SINGLE-VALUE )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.9 NAME ( 'mailSieveRuleSource' )
  DESC 'Sun ONE Messaging Server defined attribute'
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26  X-ORIGIN 'Sun ONE Messaging Server' )
olcAttributeTypes: ( 1.3.6.1.4.1.29426.1.10.10 NAME 'mailForwardingAddress'
  DESC 'Address(es) to forward all incoming messages to.'
  EQUALITY caseIgnoreIA5Match
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.26{320} )
#
# Objects: 1.3.6.1.4.1.29426.1.2.2.x
#
olcObjectClasses: ( 1.3.6.1.4.1.29426.1.2.2.1 NAME 'PostfixBookMailAccount'
  SUP top AUXILIARY
  DESC 'Mail account used in Postfix Book'
  MUST ( mail )
  MAY ( mailHomeDirectory $ mailAlias $ mailGroupMember
  $ mailUidNumber $ mailGidNumber $ mailEnabled
  $ mailQuota $mailStorageDirectory $mailSieveRuleSource ) )
olcObjectClasses: ( 1.3.6.1.4.1.29426.1.2.2.2 NAME 'PostfixBookMailForward'
  SUP top AUXILIARY
  DESC 'Mail forward used in Postfix Book'
  MUST ( mail $ mailAlias )
  MAY ( mailForwardingAddress ))

"""

def permissionsSchema(base_dn):
    return """dn: olcDatabase={1}mdb,cn=config
changeType: modify
delete: olcAccess
-
add: olcAccess
olcAccess: to attrs=userPassword,shadowLastChange 
  by self =xw 
  by dn="cn=admin,%s" write
  by group.exact="cn=Administrators,ou=Security,ou=Groups,%s" write
  by anonymous auth 
  by * none
olcAccess: to * 
  by self write 
  by dn="cn=admin,%s" write
  by group.exact="cn=Administrators,ou=Security,ou=Groups,%s" write
  by group.exact="cn=Services,ou=Security,ou=Groups,%s" write
  by * read
olcAccess: to * 
  by self read 
  by dn="cn=admin,%s" write 
  by group.exact="cn=Administrators,ou=Security,ou=Groups,%s" write
  by group.exact="cn=Services,ou=Security,ou=Groups,%s" write
  by * none


dn: cn=config
changetype: modify
add: olcAuthzPolicy
olcAuthzPolicy: to
""" % (base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn)

def initialLDIF(base_dn, domain_name, it_password):
    return """
dn: ou=Accounts,%s
objectclass: organizationalUnit
objectclass: top
ou: Accounts

dn: ou=Service,ou=Accounts,%s
objectclass: organizationalUnit
objectclass: top
ou: Service

dn: ou=User,ou=Accounts,%s
objectclass: organizationalUnit
objectclass: top
ou: User

dn: cn=IT Support,ou=User,ou=Accounts,%s
cn: IT Support
gidnumber: 500
givenname: IT
homedirectory: /home/users/itsupport
loginshell: /bin/bash
mail: itsupport@%s
objectclass: inetOrgPerson
objectclass: posixAccount
objectclass: PostfixBookMailAccount
sn: Support
uid: itsupport
uidnumber: 1000
mailEnabled: TRUE
userpassword: {CRYPT}%s

dn: ou=Groups,%s
objectclass: organizationalUnit
objectclass: top
ou: Groups

dn: ou=Security,ou=Groups,%s
objectclass: organizationalUnit
objectclass: top
ou: Security

dn: cn=Administrators,ou=Security,ou=Groups,%s
cn: Administrators
gidnumber: 500
objectclass: groupOfNames
objectclass: extensibleObject
member: cn=IT Support,ou=User,ou=Accounts,%s
authzTo: ldap:///%s??sub?(objectclass=*)

dn: cn=Users,ou=Security,ou=Groups,%s
cn: Users
gidnumber: 501
objectclass: groupOfNames
objectclass: extensibleObject
member: cn=IT Support,ou=User,ou=Accounts,%s

dn: cn=Services,ou=Security,ou=Groups,%s
cn: Services
gidnumber: 502
objectclass: groupOfNames
objectclass: extensibleObject
saslAuthzTo: ldap:///%s??sub?(objectclass=*)
member: 

dn: cn=SSO Admins,ou=Security,ou=Groups,%s
cn: SSO Admins
gidnumber: 503
objectclass: groupOfNames
objectclass: extensibleObject
member: cn=IT Support,ou=User,ou=Accounts,%s

dn: cn=Cloud Admins,ou=Security,ou=Groups,%s
cn: Cloud Admins
gidnumber: 504
objectclass: groupOfNames
objectclass: extensibleObject
member: cn=IT Support,ou=User,ou=Accounts,%s

dn: cn=VPN Users,ou=Security,ou=Groups,%s
cn: VPN Users
gidnumber: 504
objectclass: groupOfNames
objectclass: extensibleObject
member: cn=IT Support,ou=User,ou=Accounts,%s

dn: ou=Mail,ou=Groups,%s
objectclass: organizationalUnit
objectclass: top
ou: Mail

""" % (
   base_dn, base_dn, base_dn, base_dn, domain_name, sha512_crypt(it_password), base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn, base_dn
)