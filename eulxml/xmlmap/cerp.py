# file eulxml/xmlmap/cerp.py
#
#   Copyright 2010,2011 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import unicode_literals
import codecs
import datetime
import email
import logging
import os

import six

from eulxml import xmlmap
from eulxml.utils.compat import u

logger = logging.getLogger(__name__)

# CERP is described at http://siarchives.si.edu/cerp/ . XML spec available at
# http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html
# schema resolves but appears to be empty as of April 2016
# Current schema : http://www.history.ncdcr.gov/SHRAB/ar/emailpreservation/mail-account/mail-account.xsd
# internally-reused and general-utility objects
#

class _BaseCerp(xmlmap.XmlObject):
    'Common CERP namespace declarations'
    ROOT_NS = 'http://www.archives.ncdcr.gov/mail-account'
    ROOT_NAMESPACES = { 'xm': ROOT_NS }


class Parameter(_BaseCerp):
    ROOT_NAME = 'Parameter'
    name = xmlmap.StringField('xm:Name')
    value = xmlmap.StringField('xm:Value')

    def __str__(self):
        return '%s=%s' % (self.name, self.value)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, str(self))


class Header(_BaseCerp):
    ROOT_NAME = 'Header'
    name = xmlmap.StringField('xm:Name')
    value = xmlmap.StringField('xm:Value')
    comments = xmlmap.StringListField('xm:Comments')

    def __str__(self):
        return '%s: %s' % (self.name, self.value)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class _BaseBody(_BaseCerp):
    '''Common email header elements'''
    content_type_list = xmlmap.StringListField('xm:ContentType')
    charset_list = xmlmap.StringListField('xm:Charset')
    content_name_list = xmlmap.StringListField('xm:ContentName')
    content_type_comments_list = xmlmap.StringListField('xm:ContentTypeComments')
    content_type_param_list = xmlmap.NodeListField('xm:ContentTypeParam', Parameter)
    transfer_encoding_list = xmlmap.StringListField('xm:TransferEncoding')
    transfer_encoding_comments_list = xmlmap.StringListField('xm:TransferEncodingComments')
    content_id_list = xmlmap.StringListField('xm:ContentId')
    content_id_comments_list = xmlmap.StringListField('xm:ContentIdComments')
    description_list = xmlmap.StringListField('xm:Description')
    description_comments_list = xmlmap.StringListField('xm:DescriptionComments')
    disposition_list = xmlmap.StringListField('xm:Disposition')
    disposition_file_name_list = xmlmap.StringListField('xm:DispositionFileName')
    disposition_comments_list = xmlmap.StringListField('xm:DispositionComments')

    disposition_params = xmlmap.NodeListField('xm:DispositionParams', Parameter)
    other_mime_headers = xmlmap.NodeListField('xm:OtherMimeHeader', Header)


class Hash(_BaseCerp):
    ROOT_NAME = 'Hash'
    HASH_FUNCTION_CHOICES = [ 'MD5', 'WHIRLPOOL', 'SHA1', 'SHA224',
                              'SHA256', 'SHA384', 'SHA512', 'RIPEMD160']

    value = xmlmap.StringField('xm:Value')
    function = xmlmap.StringField('xm:Function',
            choices=HASH_FUNCTION_CHOICES)

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.function)


class _BaseExternal(_BaseCerp):
    '''Common external entity reference elements'''
    EOL_CHOICES = [ 'CR', 'LF', 'CRLF' ]

    rel_path = xmlmap.StringField('xm:RelPath')
    eol = xmlmap.StringField('xm:Eol', choices=EOL_CHOICES)
    hash = xmlmap.NodeField('xm:Hash', Hash)


class _BaseContent(_BaseCerp):
    '''Common content encoding elements'''
    charset_list = xmlmap.StringListField('xm:CharSet')
    transfer_encoding_list = xmlmap.StringListField('xm:TransferEncoding')


#
# messages and bodies
#

class BodyContent(_BaseContent):
    ROOT_NAME = 'BodyContent'
    content = xmlmap.StringField('xm:Content')


class ExtBodyContent(_BaseExternal, _BaseContent):
    ROOT_NAME = 'ExtBodyContent'
    local_id = xmlmap.IntegerField('xm:LocalId')
    xml_wrapped = xmlmap.SimpleBooleanField('xm:XMLWrapped',
            true='1', false='0')


class SingleBody(_BaseBody):
    ROOT_NAME = 'SingleBody'

    body_content = xmlmap.NodeField('xm:BodyContent', BodyContent)
    ext_body_content = xmlmap.NodeField('xm:ExtBodyContent', ExtBodyContent)
    child_message = xmlmap.NodeField('xm:ChildMessage', None) # this will be fixed below
    @property
    def content(self):
        return self.body_content or \
               self.ext_body_content or \
               self.child_message

    phantom_body = xmlmap.StringField('xm:PhantomBody')


class MultiBody(_BaseCerp):
    ROOT_NAME = 'MultiBody'
    preamble = xmlmap.StringField('xm:Preamble')
    epilogue = xmlmap.StringField('xm:Epilogue')

    single_body = xmlmap.NodeField('xm:SingleBody', SingleBody)
    multi_body = xmlmap.NodeField('xm:MultiBody', 'self')
    @property
    def body(self):
        return self.single_body or self.multi_body


class Incomplete(_BaseCerp):
    ROOT_NAME = 'Incomplete'
    error_type = xmlmap.StringField('xm:ErrorType')
    error_location = xmlmap.StringField('xm:ErrorLocation')

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.error_type)


class _BaseMessage(_BaseCerp):
    '''Common message elements'''
    local_id = xmlmap.IntegerField('xm:LocalId')
    message_id = xmlmap.StringField('xm:MessageId')
    message_id_supplied = xmlmap.SimpleBooleanField('xm:MessageId/@Supplied',
            true='1', false=None)
    mime_version = xmlmap.StringField('xm:MimeVersion')
    orig_date_list = xmlmap.StringListField('xm:OrigDate') # FIXME: really datetime
    # NOTE: eulxml.xmlmap.DateTimeField supports specifying format,
    # but we might need additional work since %z only works with
    # strftime, not strptime
    from_list = xmlmap.StringListField('xm:From')
    sender_list = xmlmap.StringListField('xm:Sender')
    to_list = xmlmap.StringListField('xm:To')
    cc_list = xmlmap.StringListField('xm:Cc')
    bcc_list = xmlmap.StringListField('xm:Bcc')
    in_reply_to_list = xmlmap.StringListField('xm:InReplyTo')
    references_list = xmlmap.StringListField('xm:References')
    subject_list = xmlmap.StringListField('xm:Subject')
    comments_list = xmlmap.StringListField('xm:Comments')
    keywords_list = xmlmap.StringListField('xm:Keywords')
    headers = xmlmap.NodeListField('xm:Header', Header)

    single_body = xmlmap.NodeField('xm:SingleBody', SingleBody)
    multi_body = xmlmap.NodeField('xm:MultiBody', MultiBody)
    @property
    def body(self):
        return self.single_body or self.multi_body

    incomplete_list = xmlmap.NodeField('xm:Incomplete', Incomplete)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                self.message_id or self.local_id or '(no id)')


class Message(_BaseMessage, _BaseExternal):
    """A single email message in a :class:`Folder`."""

    ROOT_NAME = 'Message'
    STATUS_FLAG_CHOICES = [ 'Seen', 'Answered', 'Flagged', 'Deleted',
                            'Draft', 'Recent']
    status_flags = xmlmap.StringListField('xm:StatusFlag',
            choices=STATUS_FLAG_CHOICES)

    @classmethod
    def from_email_message(cls, message, local_id=None):
        '''
        Convert an :class:`email.message.Message` or compatible message
        object into a CERP XML :class:`eulxml.xmlmap.cerp.Message`. If an
        id is specified, it will be stored in the Message <LocalId>.

        :param message: `email.message.Message` object
        :param id: optional message id to be set as `local_id`

        :returns: :class:`eulxml.xmlmap.cerp.Message` instance populated
    	    with message information

        '''
        result = cls()
        if local_id is not None:
            result.local_id = id

        message_id = message.get('Message-Id')
        if message_id:
            result.message_id_supplied = True
            result.message_id = message_id

        result.mime_version = message.get('MIME-Version')

        dates = message.get_all('Date', [])
        result.orig_date_list.extend([parse_mail_date(d) for d in dates])

        result.from_list.extend(message.get_all('From', []))
        result.sender_list.extend(message.get_all('From', []))
        try:
            result.to_list.extend(message.get_all('To', []))
        except UnicodeError:
            print(repr(message['To']))
            raise
        result.cc_list.extend(message.get_all('Cc', []))
        result.bcc_list.extend(message.get_all('Bcc', []))
        result.in_reply_to_list.extend(message.get_all('In-Reply-To', []))
        result.references_list.extend(message.get_all('References', []))
        result.subject_list.extend(message.get_all('Subject', []))
        result.comments_list.extend(message.get_all('Comments', []))
        result.keywords_list.extend(message.get_all('Keywords', []))

        headers = [ Header(name=key, value=val) for key, val in message.items() ]
        result.headers.extend(headers)

        # FIXME: skip multipart messages for now
        if not message.is_multipart():
            result.create_single_body()

            # FIXME: this is a small subset of the actual elements CERP allows.
            # we should add the rest of them, too.

            # message.get_content_type() always returns something. only
            # put it in the CERP if a Content-Type was explicitly specified.
            if message['Content-Type']:
                result.single_body.content_type_list.append(message.get_content_type())
            if message.get_content_charset():
                result.single_body.charset_list.append(message.get_content_charset())
            if message.get_filename():
                result.single_body.content_name_list.append(message.get_filename())

            # FIXME: attaching the body_content only makes sense for text
            # content types. we'll eventually need a better solution for
            # non-text messages
            result.single_body.create_body_content()
            payload = message.get_payload(decode=False)

            # if not unicode, attempt to convert
            if isinstance(payload, six.binary_type):
                charset = message.get_charset()
                # decode according to the specified character set, if any
                if charset is not None:
                    charset_decoder = codecs.getdecoder(str(charset))
                    payload, length = charset_decoder(payload)

                # otherwise, just try to convert
                else:
                    payload = u(payload)

            # remove any control characters not allowed in XML
            control_char_map = dict.fromkeys(range(32))
            for i in [9, 10, 13]: # preserve horizontal tab, line feed, carriage return
                del control_char_map[i]

            payload = u(payload).translate(control_char_map)

            result.single_body.body_content.content = payload

        else:
            # TODO: handle multipart
            logger.warn('CERP conversion does not yet handle multipart')

        # assume we've normalized newlines:
        result.eol = EOLMAP[os.linesep]

        return result


class ChildMessage(_BaseMessage):
    ROOT_NAME = 'ChildMessage'
    # no additional elements

# Patch-up from above. FIXME: This is necessary because of recursive
# NodeFields. eulxml.xmlmap.NodeField doesn't currently support these
SingleBody.child_message.node_class = ChildMessage

#
# accounts and folders
#

class Mbox(_BaseExternal):
    ROOT_NAME = 'Mbox'
    # no additional fields


class Folder(_BaseCerp):
    """A single email folder in an :class:`Account`, composed of multiple
    :class:`Message` objects and associated metadata."""

    ROOT_NAME = 'Folder'

    name = xmlmap.StringField('xm:Name')
    messages = xmlmap.NodeListField('xm:Message', Message)
    subfolders = xmlmap.NodeListField('xm:Folder', 'self')
    mboxes = xmlmap.NodeListField('xm:Mbox', Mbox)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.name)


class ReferencesAccount(_BaseCerp):
    ROOT_NAME = 'ReferencesAccount'
    REF_TYPE_CHOICES = [ 'PreviousContent', 'SubsequentContent',
                         'Supplemental', 'SeeAlso', 'SeeInstead' ]

    href = xmlmap.StringField('xm:Href')
    email_address = xmlmap.StringField('xm:EmailAddress')
    reference_type = xmlmap.StringField('xm:RefType',
            choices=REF_TYPE_CHOICES)


class Account(_BaseCerp):
    """A single email account associated with a single email address and
    composed of multiple :class:`Folder` objects and additional metadata."""

    ROOT_NAME = 'Account'
    XSD_SCHEMA = 'http://www.history.ncdcr.gov/SHRAB/ar/emailpreservation/mail-account/mail-account.xsd'

    email_address = xmlmap.StringField('xm:EmailAddress')
    global_id = xmlmap.StringField('xm:GlobalId')
    references_accounts = xmlmap.NodeListField('xm:ReferencesAccount',
            ReferencesAccount)
    folders = xmlmap.NodeListField('xm:Folder', Folder)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                self.global_id or self.email_address or '(no id)')




def parse_mail_date(datestr):
    '''Helper method used by :meth:`Message.from_email_message` to
    convert dates from rfc822 format to iso 8601.

    :param datestr: string containing a date in rfc822 format
    :returns: string with date in iso 8601 format
    '''

    time_tuple = email.utils.parsedate_tz(datestr)
    if time_tuple is None:
        return datestr
    dt = datetime.datetime.fromtimestamp(email.utils.mktime_tz(time_tuple))
    return dt.isoformat()

EOLMAP = {
    '\r': 'CR',
    '\n': 'LF',
    '\r\n': 'CRLF',
}
