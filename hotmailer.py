#!/usr/bin/env python3

import logging
logging.basicConfig( level=logging.DEBUG ) # DEBUG HERE

import argparse, datetime, math, multiprocessing, random, re, sys, textwrap, time

import imaplib, smtplib
import email, email.mime.multipart, email.mime.text

import faker, nltk

COUNTER={}
LOCAL_ACCOUNTS=[]
HOTMAIL_ACCOUNTS=[]
LOCAL_SMTP_HOSTNAME=""
LOCAL_SMTP_PORT=587
LOCAL_IMAP_HOSTNAME=LOCAL_SMTP_HOSTNAME
LOCAL_IMAP_PORT=993
HOTMAIL_SMTP_HOSTNAME="smtp-mail.outlook.com"
HOTMAIL_SMTP_PORT=587
HOTMAIL_IMAP_HOSTNAME="imap-mail.outlook.com"
HOTMAIL_IMAP_PORT=993
SMTP_EHLO=""
DESTINATION_FOLDER="seeding"

MAIL_DEBUG=False # DEBUG HERE
REPLY_LIKELINESS=8 # out of 10, 10 being high (and 100%)
DELAY_LOOP_SECONDS=range( 300, 1200 ) # TUNING HERE
DELAY_ACTION_SECONDS=range( 30, 45 ) # TUNING HERE
DELIVERY_THRESHOLD_MULTIPLIER=1.5
UNREAD_SCAN_MAX=10
MAX_REFERENCES=3
SUBJECT_WORD_MINIMUM=5
SUBJECT_WORD_MAXIMUM=12
BODY_WIDTH_MINIMUM=70
BODY_WIDTH_MAXIMUM=130
BODY_RANDOM_SYNONYM_PROBABILITY=5 # out of 10, 10 being high (and 100%)
BODY_QUOTE_PROBABILITY=8
BODY_PARAGRAPHS_MINIMUM=1
BODY_PARAGRAPHS_MAXIMUM=5
PARAGRAPH_SENTENCES_MINIMUM=5
PARAGRAPH_SENTENCES_MAXIMUM=12
MAX_PROCESSES_MULTIPLIER=3 # TUNING HERE

class TracedException( Exception ): pass

# drop a 'debugger()' call before an intended break point for awesomeness
def debugger(): import pdb; pdb.set_trace()

def counter_increment( email ): # *** ONLY TO BE CALLED FROM MAIN PROCESS ***
    if email in COUNTER: COUNTER[ email ] += 1
    else: COUNTER[ email ] = 1

def add_account( local_or_hotmail, account ):
    if local_or_hotmail == "LOCAL": LOCAL_ACCOUNTS.append( account )
    elif local_or_hotmail == "HOTMAIL": HOTMAIL_ACCOUNTS.append( account )
    else: raise TracedException( "typo's abound!" )

def generate_synonym( word ):
    if len( word ) > 3 and word.isalpha():
        words = []
        for synonym in nltk.corpus.wordnet.synsets( word ):
            for leema in synonym.lemmas():
                words.append( leema.name() )
        if len( words ) < 1: return word
        else: return random.choice( words ).replace( "_", " " )
    else: return word

def generate_sentences( files, count ):
    sentences = []
    while len( sentences ) < count:
        for split in random_read_file_lines( random.choice( files ), 1 )[ 0 ].split( "." ):
            if len( split ) < 5: continue
            sentences.append( split )
            if len( sentences ) == count: break
    return sentences

def generate_paragraphs( sentences, minimum, maximum ):
    paragraphs = []
    while len( sentences ) > 0:
        amount = random.randint( minimum, maximum )
        if len( sentences ) > amount:
            paragraphs.append( ".".join( [ sentences.pop() for i in range( amount ) ] ) )
        else:
            paragraphs.append( ".".join( sentences ) + "." )
            break
    return paragraphs

def generate_greeting():
    greetings = [ "Hello", "Hi" ]
    return random.choice( greetings )

def generate_farewell():
    farewells = [ "Sincerly", "Regards", "Faithfully" ]
    if random.randint( 0, 9 ) < 6: return random.choice( farewells )
    else: return "Yours {farewall}".format( farewall=random.choice( farewells ) )

def generate_name(): return faker.Faker().name()

def generate_agent(): return random_read_file_lines( "data/agents.txt", 1 )[ 0 ]

def generate_subject( sentences ):
    punctuation = [ "/", "%", "-", "--" ] # do not put a colon in here
    words = [ "test", "subject", "seed" ]
    sentence = random.choice( sentences )
    if len( sentence ) > 5:
        return " ".join(
            random_synonyms( re.sub( r"[^\w\s]", "", sentence ), 5 ).split( " " )[
                0:random.randint( SUBJECT_WORD_MINIMUM, SUBJECT_WORD_MAXIMUM )
            ]
        ).strip()
    else:
        return random_synonyms(
            "{a1} {p1} {a2} {p2} {a3} {p3} {a4} {a5}".format(
                a1=random.choice( [ random.choice( words ), random.randint( 0, 100 ) ] ),
                a2=random.choice( [ random.choice( words ), random.randint( 0, 100 ) ] ),
                a3=random.choice( [ random.choice( words ), random.randint( 0, 100 ) ] ),
                a4=random.choice( [ random.choice( words ), random.randint( 0, 100 ) ] ),
                a5=random.choice( [ random.choice( words ), random.randint( 0, 100 ) ] ),
                p1=random.choice( punctuation ), p2=random.choice( punctuation ),
                p3=random.choice( punctuation )
            ), 5
        )

def generate_body( files, minimum, maximum, source, destination ):
    spacing = random.choice( [ "\n", "\n\n", "\n\n\n" ] )
    indent = random.choice( [ "", "  ", "    ", "\t" ] )
    width = random.randint( BODY_WIDTH_MINIMUM, BODY_WIDTH_MAXIMUM )

    count = random.randint( minimum, maximum )

    sentences = [ random_synonyms( sentence, BODY_RANDOM_SYNONYM_PROBABILITY ) for sentence in generate_sentences( files, 100 ) ]

    paragraphs = generate_paragraphs( sentences, PARAGRAPH_SENTENCES_MINIMUM, PARAGRAPH_SENTENCES_MAXIMUM )[ 0:( count - 1 ) ]

    text = "{greeting} {destination},\n\n".format( greeting=generate_greeting(), destination=destination )
    for paragraph in paragraphs:
        for wrapped in textwrap.wrap( paragraph, width=width, break_long_words=False ):
            text += "{indent}{text}\n".format( indent=indent, text=wrapped )
        text += spacing
    text += "{farewell},\n{source}".format( farewell=generate_farewell(), source=source )
    
    return { "sentences": sentences, "paragraphs": paragraphs, "text": text }

def generate_quote( text ):
    if type( text ) == str and len( text ) > 10:
        quotes = [ ">", ">", ">", "|", "-" ]
        quote = random.choice( quotes )
        spacing = random.choice( [ "", " ", "  " ] )
        return "\n".join(
            [
                "{quote}{spacing}{line}".format(
                    quote=quote, spacing=spacing, line=line
                ) for line in text.splitlines()
            ]
        )
    else: return ""

def random_synonyms( sentence, probability ):
    processed = []
    for word in sentence.split( " " ):
        if probability > random.randint( 0, 9 ) and len( word ) > 3 and word.isalpha():
            processed.append( generate_synonym( word ) )
        else: processed.append( word )
    return " ".join( processed )

def random_read_file_lines( filename, count ):
    lines = []
    while len( lines ) < count:
        lines.append( random.choice( open( filename ).readlines() ).strip() )
    return lines

def random_read_multiple_file_lines( filenames, count ):
    lines = []
    while len( lines ) < count:
        lines.append( random_read_file_lines( random.choice( filenames ), 1 ) )
    return lines

def random_do_reply(): return True if REPLY_LIKELINESS > random.randint( 0, 9 ) else False

def random_delay( variable ): time.sleep( random.choice( variable ) )

def smtp_connect_tls( hostname, port ):
    reference = smtplib.SMTP( hostname, port=port )
    if MAIL_DEBUG: reference.set_debuglevel( 1 )
    smtp_ehlo( reference )
    reference.starttls()
    smtp_ehlo( reference )
    return reference

def smtp_connect_ssl( hostname, port ):
    reference = smtplib.SMTP_SSL( hostname, port=port )
    if MAIL_DEBUG: reference.set_debuglevel( 1 )
    smtp_ehlo( reference )
    return reference

def smtp_ehlo( reference ): reference.ehlo( SMTP_EHLO )

def smtp_login( reference, username, password ):
    reference.esmtp_features[ "auth" ] = "PLAIN LOGIN"
    reference.login( username, password )

def smtp_simple_login_test( local_or_hotmail, credentials ):
    try:
        if local_or_hotmail == "LOCAL":
            reference = smtp_connect_tls( LOCAL_SMTP_HOSTNAME, LOCAL_SMTP_PORT )
        elif local_or_hotmail == "HOTMAIL":
            reference = smtp_connect_tls( HOTMAIL_SMTP_HOSTNAME, HOTMAIL_SMTP_PORT )
        else: raise TracedException( "typo's abound!" )
        smtp_login( reference, credentials[ "email" ], credentials[ "password" ] )
        smtp_disconnect( reference )
    except: return False
    return True

def smtp_simple_connect( local_or_hotmail, credentials ):
    if local_or_hotmail == "LOCAL":
        reference = smtp_connect_tls( LOCAL_SMTP_HOSTNAME, LOCAL_SMTP_PORT )
    elif local_or_hotmail == "HOTMAIL":
        reference = smtp_connect_tls( HOTMAIL_SMTP_HOSTNAME, HOTMAIL_SMTP_PORT )
    else: raise TracedException( "typo's abound!" )
    smtp_login( reference, credentials[ "email" ], credentials[ "password" ] )
    return reference

def smtp_disconnect( reference ):
    try: reference.quit()
    except: pass
    finally: del reference

def smtp_standard_headers( source, destination, subject, agent ):
    return { "From": source, "To": destination, "Subject": subject, "User-Agent": agent }

def smtp_send( reference, message ):
    reference.sendmail( message[ "From" ], message[ "To" ], message.as_string() )

def smtp_simple_send( local_or_hotmail, credentials, headers, body, html=False ):
    reference = smtp_simple_connect( local_or_hotmail, credentials )
    message = email.mime.multipart.MIMEMultipart( "alternative" )
    for key, value in headers.items(): message[ key ] = value
    message.attach( email.mime.text.MIMEText( body, "plain" ) )
    if html:
        message.attach(
            email.mime.text.MIMEText(
                "<html><head></head><body>{text}</body></html>".format(
                    text=body.replace( "\n", "<br/>" )
                ),
                "html"
            )
        )
    smtp_send( reference, message )

def imap_connect_tls( hostname, port ):
    reference = imaplib.IMAP4( hostname, port=port )
    reference.starttls()
    return reference

def imap_connect_ssl( hostname, port ):
    reference = imaplib.IMAP4_SSL( hostname, port=port )
    return reference

def imap_login( reference, username, password ):
    reference.login( username, password )

def imap_simple_login_test( local_or_hotmail, credentials ):
    try:
        if local_or_hotmail == "LOCAL":
            reference = imap_connect_tls( LOCAL_IMAP_HOSTNAME, LOCAL_IMAP_PORT )
        elif local_or_hotmail == "HOTMAIL":
            reference = imap_connect_ssl( HOTMAIL_IMAP_HOSTNAME, HOTMAIL_IMAP_PORT )
        else: raise TracedException( "typo's abound!" )
        imap_login( reference, credentials[ "email" ], credentials[ "password" ] )
        imap_disconnect( reference )
    except: return False
    return True

def imap_simple_connect( local_or_hotmail, credentials ):
    if MAIL_DEBUG: imaplib.Debug = 4
    if local_or_hotmail == "LOCAL":
        reference = imap_connect_tls( LOCAL_IMAP_HOSTNAME, LOCAL_IMAP_PORT )
    elif local_or_hotmail == "HOTMAIL":
        reference = imap_connect_ssl( HOTMAIL_IMAP_HOSTNAME, HOTMAIL_IMAP_PORT )
    else: raise TracedException( "typo's abound!" )
    imap_login( reference, credentials[ "email" ], credentials[ "password" ] )
    return reference

def imap_disconnect( reference ):
    try: reference.close(); reference.logout()
    except: pass
    finally: del reference

def imap_expunge( reference, folder ):
    imap_select( reference, folder, readonly=False )
    reference.expunge()
    imap_select( reference, folder, readonly=True )

def imap_select( reference, folder, readonly=True ):
    reference.select( folder, readonly=readonly )

def imap_search( reference, folder, criteria ):
    imap_select( reference, folder )
    response, results = reference.search( None, criteria )
    for message_number in results[ 0 ].split(): yield int( message_number.decode( "ascii" ) )

def imap_fetch_one_uid( reference, folder, message_number ):
    imap_select( reference, folder )
    response, results = reference.fetch( str( message_number ).encode( "ascii" ), "(UID)" )
    if len( results ) == 2: return results[ 0 ][ 1 ].decode( "ascii" )
    else: raise TracedException( "to many messages returned" )

def imap_fetch_one( reference, folder, message_number ):
    imap_select( reference, folder )
    response, results = reference.fetch( str( message_number ).encode( "ascii" ), "(RFC822)" )
    if len( results ) == 2: return email.message_from_string( results[ 0 ][ 1 ].decode( "ascii" ) )
    else: raise TracedException( "to many messages returned" )

def imap_fetch_multi( reference, folder, message_numbers ):
    imap_select( reference, folder )
    response, results = reference.fetch( ",".join( message_number ).encode( "ascii" ), "(RFC822)" )
    for result in results: yield email.message_from_string( result[ 0 ][ 1 ].decode( "ascii" ) )

def imap_folder_has_unread( reference, folder ):
    imap_select( reference, folder )
    response, results = reference.status( folder, "(UNSEEN)" )
    return False if "UNSEEN 0" in str( results[ 0 ] ) else True

def imap_list_folder_generator( reference, folder, criteria ):
    for message_number in imap_search( reference, folder, criteria ): yield message_number

def imap_list_folder_unread_generator( reference, folder ):
    if imap_folder_has_unread( reference, folder ):
        yield from imap_list_folder_generator( reference, folder, "UNSEEN" )

def imap_copy_mail( reference, source_folder, destination_folder, message_number ):
    imap_select( reference, source_folder, readonly=False )
    reference.copy( str( message_number ).encode( "ascii" ), destination_folder )
    imap_select( reference, source_folder, readonly=True )

def imap_move_mail( reference, source_folder, detination_folder, message_number ):
    imap_copy_mail( reference, source_folder, detination_folder, message_number )
    imap_mark_deleted( reference, source_folder, message_number )
    imap_expunge( reference, source_folder )

def imap_list_folders( reference ):
    return [
        re.search( r'" "(.*)"$', item.decode( "ascii" ) ).groups()[ 0 ] for item in reference.list()[ 1 ]
    ]

def imap_find_latest_unread_by_source_and_subject( reference, folder, source, subject ):
    match = None
    unreads = list( imap_list_folder_unread_generator( reference, folder ) )
    if len( unreads ) < 1: raise TracedException( "no unread emails found" )
    if len( unreads ) > UNREAD_SCAN_MAX: unreads = unreads[ -UNREAD_SCAN_MAX: ]
    for unread in reversed( unreads ):
        message = imap_fetch_one( reference, folder, unread )
        if message[ "From" ] == source or "<{email}>".format( email=source ) in message[ "From" ]:
            if subject in message[ "Subject" ]:
                parsed_date = email.utils.parsedate_to_datetime( message[ "Date" ] )
                now = datetime.datetime.now( datetime.timezone.utc )
                if ( max( DELAY_LOOP_SECONDS ) * DELIVERY_THRESHOLD_MULTIPLIER ) > ( ( now - parsed_date ).seconds ):
                    match = { "number": unread, "message": message }
                    break
    if match is None: raise TracedException( "couldn't find message to reply to" )
    else: return match

def imap_has_folder( reference, name ):
    return True if name in imap_list_folders( reference ) else False

def imap_new_folder( reference, name ): # RO doesn't affect this!?
    if not imap_has_folder( reference, name ): reference.create( name )

def imap_mark( reference, folder, message_number, flags ):
    imap_select( reference, folder, readonly=False )
    reference.store( str( message_number ).encode( "ascii" ), "+FLAGS", flags )
    imap_select( reference, folder, readonly=True )

def imap_mark_read( reference, folder, message_number ):
    imap_mark( reference, folder, message_number, "\Seen" )

def imap_mark_answered( reference, folder, message_number ):
    imap_mark( reference, folder, message_number, "\Answered" )

def imap_mark_deleted( reference, folder, message_number ):
    imap_mark( reference, folder, message_number, "\Deleted" )

def send_mail( local_or_hotmail, credentials, forceheaders, body ):
    headers = smtp_standard_headers(
        forceheaders[ "From" ], forceheaders[ "To" ],
        forceheaders[ "Subject" ], forceheaders[ "User-Agent" ]
    )
    for key, value in forceheaders.items(): headers[ key ] = value
    smtp_simple_send( local_or_hotmail, credentials, headers, body, random.choice( [ True, False ] ) ) # RANDOM HERE

def send_first( accounts ):
    body = generate_body(
        [ "data/base.txt", "data/filler.txt" ],
        BODY_PARAGRAPHS_MINIMUM, BODY_PARAGRAPHS_MAXIMUM,
        generate_name(), generate_name()
    )
    subject = generate_subject( body[ "sentences" ] )
    send_mail(
        "LOCAL", accounts[ "LOCAL" ],
        smtp_standard_headers(
            accounts[ "LOCAL" ][ "email" ], accounts[ "HOTMAIL" ][ "email" ], subject, generate_agent()
        ),
        body[ "text" ]
    )
    return subject

def send_reply( local_or_hotmail, accounts, references, subject ):
    alt = "LOCAL" if local_or_hotmail == "HOTMAIL" else "HOTMAIL"
    folder = "INBOX"
    
    reference = imap_simple_connect( alt, accounts[ alt ] )
    
    match = imap_find_latest_unread_by_source_and_subject(
        reference, folder, accounts[ local_or_hotmail ][ "email" ], subject
    )
    
    headers = smtp_standard_headers(
        accounts[ alt ][ "email" ], accounts[ local_or_hotmail ][ "email" ],
        "{ref}{previous}".format(
            ref=random.choice( [ "", "RE: ", "re: ", "RE:", "FW: ", "FW:" ] ),
            previous=random.choice([
                match[ "message" ][ "Subject" ].split( ":" )[ -1 ],
                match[ "message" ][ "Subject" ], match[ "message" ][ "Subject" ], match[ "message" ][ "Subject" ]
            ])
        ),
        generate_agent()
    )
    headers[ "In-Reply-To" ] = match[ "message" ][ "Message-ID" ]
    headers[ "References" ] = "{latest} {previous}".format(
        latest=match[ "message" ][ "Message-ID" ],
        previous=" ".join( reversed( references[ -MAX_REFERENCES: ] ) )
    )

    body = generate_body(
        [ "data/reply.txt", "data/filler.txt" ],
        BODY_PARAGRAPHS_MINIMUM, BODY_PARAGRAPHS_MAXIMUM,
        generate_name(), generate_name()
    )

    # this uglyness needs fixing, eurgh!
    if match[ "message" ].is_multipart(): quote = match[ "message" ].get_payload( 0 )
    else: quote = match[ "message" ].get_payload()
    quote = generate_quote( quote ) if BODY_QUOTE_PROBABILITY > random.randint( 0, 9 ) else ""

    random_delay( DELAY_ACTION_SECONDS ) # simulate reading
    imap_mark_read( reference, folder, match[ "number" ] )

    random_delay( DELAY_ACTION_SECONDS ) # simulate replying
    send_mail( alt, accounts[ alt ], headers, "{body}\n\n{quote}".format( body=body[ "text" ], quote=quote ) )
    imap_mark_answered( reference, folder, match[ "number"  ] )

    random_delay( DELAY_ACTION_SECONDS ) # simulate life
    imap_move_mail( reference, folder, DESTINATION_FOLDER, match[ "number" ] )

    imap_disconnect( reference )

    return match[ "message" ][ "Message-ID" ]

def send_reply_loop( messages ):
    try:
        start = datetime.datetime.now()
        
        sender = "LOCAL"; sender_alt = "HOTMAIL"
        accounts = {
            "LOCAL": random.choice( LOCAL_ACCOUNTS ),
            "HOTMAIL": random.choice( HOTMAIL_ACCOUNTS )
        }
        
        subject = send_first( accounts )
        messages.put( accounts[ sender ][ "email" ] )
        
        references = []
        while random_do_reply():
            random_delay( DELAY_LOOP_SECONDS )
            references.append( send_reply( sender, accounts, references, subject ) )
            messages.put( accounts[ sender_alt ][ "email" ] )
            sender, sender_alt = sender_alt, sender

        print(
            "{date}: '{count}' messages sent in chain over '{time}' minutes with refs '{refs}'\n".format(
                date=datetime.datetime.now(),
                count=len( references ) + 1,
                time=math.ceil( ( datetime.datetime.now() - start ).total_seconds() / 60 ),
                refs=" -> ".join([
                    "{first}...{last}".format(
                        first=reference[ 0:7 ], last=reference[ -7: ]
                    ) for reference in references
                ])
            )
        )
    except Exception as exception: return str( exception )
    return True

def setup_and_check():
    for service in ( ( "LOCAL", LOCAL_ACCOUNTS ), ( "HOTMAIL", HOTMAIL_ACCOUNTS ) ):
        for credential in service[ 1 ]:
            if not imap_simple_login_test( service[ 0 ], credential ): return False
            if not smtp_simple_login_test( service[ 0 ], credential ): return False

            try:
                reference = imap_simple_connect( service[ 0 ], credential )
                imap_new_folder( reference, DESTINATION_FOLDER )
                imap_disconnect( reference )
            except: return False
    return True

def mainloop():
    if not setup_and_check():
        print( "account testing failed, check credentials and try again" )
        sys.exit( 1 )

    while True:
        queue_manager = multiprocessing.Manager()
        messages = queue_manager.Queue()
        
        runners = max( [ len( LOCAL_ACCOUNTS ), len( HOTMAIL_ACCOUNTS ) ] ) * MAX_PROCESSES_MULTIPLIER
        
        workers = multiprocessing.Pool( processes = runners )
        worker_results = []

        for index in range( runners ):
            worker_results.append( workers.apply_async( send_reply_loop, ( messages, ) ) )
        
        while True:
            ready = True
            for worker_result in worker_results:
                if not worker_result.ready(): ready = False
            if ready: break
            else: time.sleep( 0.5 )
        
        while not messages.empty(): counter_increment( messages.get() )

        for worker_result in worker_results:
            result = worker_result.get()
            if not result: print( "loop failed with '{message}'", message=result )

        # http://stackoverflow.com/questions/9959598/multiprocessing-and-garbage-collection/35784070#35784070
        del worker_results; del workers; del messages; del queue_manager
        
        for value in COUNTER.values():
            if value > 270: # hotmail will trip at 300!!!
                print( COUNTER + "\n\n... that's getting a little close, check the tuning variables" )
                sys.exit( 1 )

parser = argparse.ArgumentParser()
parser.add_argument( "local_accounts", type=str, help="email:password|email:password|..." )
parser.add_argument( "hotmail_accounts", type=str, help="email:password|email:password|..." )

arguments = parser.parse_args()

for pair in ( ( "local_accounts", "LOCAL" ), ( "hotmail_accounts", "HOTMAIL" ) ):
    for account in vars( arguments )[ pair[ 0 ] ].split( "|" ):
        credentials = account.split( ":" )
        add_account( pair[ 1 ], { "email": credentials[ 0 ], "password": credentials[ 1 ] } )

mainloop()
