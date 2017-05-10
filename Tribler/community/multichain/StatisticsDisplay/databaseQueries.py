"""
This file contains all the queries used by the database driver.
"""

class DatabaseQueries(object):
    # Get all the direct neighbors of a node
    list_neighbor_query = """
            SELECT DISTINCT hex(public_key_responder) FROM multi_chain where hex(public_key_requester) = ?
            UNION
            SELECT DISTINCT hex(public_key_requester) FROM multi_chain where hex(public_key_responder) = ?
            """

    # Query to find how much a node uploaded to others
    total_self_up_query = "SELECT sum(up) FROM multi_chain where hex(public_key_requester) = ?"
    # Query to find how much a ohters downloaded from a node
    total_other_down_query = "SELECT sum(down) FROM multi_chain WHERE hex(public_key_responder = ?)"
   
    # Query to find how much a node downloaded to others
    total_self_down_query = "SELECT sum(down) FROM multi_chain where hex(public_key_requester) = ?"
    # Query to find how much others uploaded to a node
    total_other_up_query = "SELECT sum(up) FROM multi_chain WHERE hex(public_key_responder = ?)"
   
    # Query to find how much a node uploaded to a neighbor
    neighbor_self_up_query = "SELECT sum(up) FROM multi_chain WHERE hex(public_key_requester) = ?" \
                             "AND hex(public_key_responder) = ?"
    # Query to find how much a neighbor downloaded from a node
    neighbor_other_down_query = "SELECT sum(down) FROM multi_chain WHERE hex(public_key_responder) = ?" \
                                "AND hex(public_key_requester) = ?"
   
    # Query to find how much a node downloaded from a neighbor
    neighbor_self_down_query = "SELECT sum(down) FROM multi_chain WHERE hex(public_key_requester) = ?" \
                               "AND hex(public_key_responder) = ?"
    # Query to find how much a neighbor uploaded to a node
    neighbor_other_up_query = "SELECT sum(up) FROM multi_chain WHERE hex(public_key_responder) = ?" \
                              "AND hex(public_key_requester) = ?"
   
    # Queries to create a dummy database

    # Create table for dummy data
    create_table_query = """
    CREATE TABLE IF NOT EXISTS multi_chain(
     public_key_requester		TEXT NOT NULL,
     public_key_responder		TEXT NOT NULL,
     up                         INTEGER NOT NULL,
     down                       INTEGER NOT NULL,
    
     total_up_requester         UNSIGNED BIG INT NOT NULL,
     total_down_requester       UNSIGNED BIG INT NOT NULL,
     sequence_number_requester  INTEGER NOT NULL,
     previous_hash_requester	TEXT NOT NULL,
     signature_requester		TEXT NOT NULL,
     hash_requester		        TEXT PRIMARY KEY,
    
     total_up_responder         UNSIGNED BIG INT NOT NULL,
     total_down_responder       UNSIGNED BIG INT NOT NULL,
     sequence_number_responder  INTEGER NOT NULL,
     previous_hash_responder	TEXT NOT NULL,
     signature_responder		TEXT NOT NULL,
     hash_responder		        TEXT NOT NULL,
    
     insert_time                TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
     )
    """

    # Insert the dummy data in the database
    insert_data_query = """
    INSERT INTO multi_chain (public_key_requester, public_key_responder, up, down, total_up_requester, total_down_requester,
    sequence_number_requester, previous_hash_requester, signature_requester, hash_requester, total_up_responder,
    total_down_responder, sequence_number_responder, previous_hash_responder, signature_responder, hash_responder) VALUES
    ('0', '1',  10,   5,    0, 0, 0, '', '', 'a', 0, 0, 0, 'a', '', ''),
    ('1', '0',  3,    6,    0, 0, 0, '', '', 'b', 0, 0, 0, 'a', '', ''),
    ('1', '0',  46,   12,   0, 0, 0, '', '', 'c', 0, 0, 0, 'a', '', ''),
    
    ('0', '2',  123,  6,    0, 0, 0, '', '', 'd', 0, 0, 0, 'a', '', ''),
    ('2', '0',  21,   3,    0, 0, 0, '', '', 'e', 0, 0, 0, 'a', '', ''),
    
    ('0', '3',  22,   68,   0, 0, 0, '', '', 'f', 0, 0, 0, 'a', '', ''),
    ('3', '0',  234,  12,   0, 0, 0, '', '', 'g', 0, 0, 0, 'a', '', ''),
    
    ('0', '4',  57,   357,  0, 0, 0, '', '', 'h', 0, 0, 0, 'a', '', ''),
    ('4', '0',  223,  2,    0, 0, 0, '', '', 'i', 0, 0, 0, 'a', '', ''),
    
    ('1', '5',  13,   5,    0, 0, 0, '', '', 'j', 0, 0, 0, 'a', '', ''),
    ('5', '1',  14,   6,    0, 0, 0, '', '', 'k', 0, 0, 0, 'a', '', ''),
    
    ('1', '6',  234,  5,    0, 0, 0, '', '', 'l', 0, 0, 0, 'a', '', ''),
    
    ('1', '10', 102,  5,    0, 0, 0, '', '', 'm', 0, 0, 0, 'a', '', ''),
    ('10','1',  123,  0,    0, 0, 0, '', '', 'n', 0, 0, 0, 'a', '', ''),
    
    ('2', '7',  87,   5,    0, 0, 0, '', '', 'o', 0, 0, 0, 'a', '', ''),
    ('7', '2',  342,  1,    0, 0, 0, '', '', 'p', 0, 0, 0, 'a', '', ''),
    
    ('2', '8',  0,    5,    0, 0, 0, '', '', 'q', 0, 0, 0, 'a', '', ''),
    ('2', '8',  78,   23,   0, 0, 0, '', '', 'r', 0, 0, 0, 'a', '', ''),
    
    ('3', '4',  20,   5,    0, 0, 0, '', '', 's', 0, 0, 0, 'a', '', ''),
    ('4', '3',  3,    5,    0, 0, 0, '', '', 't', 0, 0, 0, 'a', '', ''),
    
    ('4', '9',  650,  5,    0, 0, 0, '', '', 'u', 0, 0, 0, 'a', '', ''),
    ('9', '4',  650,  5,    0, 0, 0, '', '', 'v', 0, 0, 0, 'a', '', ''),
    
    ('5', '6',  234,  5,    0, 0, 0, '', '', 'w', 0, 0, 0, 'a', '', ''),
    ('6', '5',  5,    323,  0, 0, 0, '', '', 'x', 0, 0, 0, 'a', '', ''),
    
    ('6', '7',  12,   5,    0, 0, 0, '', '', 'y', 0, 0, 0, 'a', '', ''),
    ('7', '6',  12,   5,    0, 0, 0, '', '', 'z', 0, 0, 0, 'a', '', ''),
    
    ('9', '10', 51,   123,  0, 0, 0, '', '', '0', 0, 0, 0, 'a', '', ''),
    ('10', '9', 76,   5,    0, 0, 0, '', '', '1', 0, 0, 0, 'a', '', '')
    """