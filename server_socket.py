#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 10 18:58:52 2018

@author: amit
"""
import constants
import model
import utils

import socket 
import threading
import json
import traceback
import client_socket

class ServerSocket(threading.Thread):
    
    server_socket = None
    host = None
    collection = None
    
    def __init__(self, port):
        threading.Thread.__init__(self)
        
        print("Instantiating server socket on port "+str(port)+" ...")
        host = '127.0.0.1'
        
        # Create a server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # get local machine name
        self.server_socket.bind((host, port))
        
        # queue up to 5 requests
        self.server_socket.listen(5)
        
        dbConn = model.PyMongoModel()
        self.collection = dbConn.getCollection("process_"+str(port))

        self.port = port
    
    def run(self):
         # initiate listening
        self.initiateListening()
        
    def initiateListening(self):
        while True:
            
            clientsocket = None
            try:
                # establish a connection
                clientsocket,addr = self.server_socket.accept()
            
                print("Got a connection from %s" % str(addr))
                msg = clientsocket.recv(4096)
                recvd_msg = json.loads(msg)
                topic = recvd_msg['topic']
                
                print("Message Topic: "+topic)
               
                # Check if invalid message received
                if topic not in constants.topic:
                    clientsocket.send(json.dumps({'topic':"Invalid message! "
                                                  +"This incident will be reported."})
                    .encode('utf-8'))
                
                elif topic == 'PING':
                   clientsocket.send(json.dumps({'topic':'PONG'}).encode('utf-8'))
                   
                elif topic == 'JOIN_REQUEST':
                    client_addr = recvd_msg['address']
                     
                    # If not server then return Address of server
                    
                    # else if server then add this to list of known addresses
                    # addresses and return membership view
                    
                    key = utils.getKey();
                    doc = self.collection.find_one()

                    
                    # if view of membership is already created
                    if doc is not None and 'viewOfMembership' in doc:
                        # search for a client with port in the local db
                        temp_doc = self.collection.find_one({"viewOfMembership": {"address":client_addr}})
                        
                        # If document already present then delete doc
                        if temp_doc is not None:
                            self.collection.delete_one({'_id':temp_doc['_id']})
                            
                        doc['viewOfMembership'].append({'address':client_addr, 'isMember':True, 'key':key})
                        doc = self.collection.update({'_id':doc['_id']}, doc)
                    else:
                        # create new document
                        doc = {}
                        doc['viewOfMembership'] = [{'address':client_addr, 'isMember':True, 'key':key}]
                        doc = self.collection.insert_one(doc)
                    
                    # send a key
                    # client_socket.send((json.dumps({"topic":'APPROVED', "key":key})).encode('utf-8'))



                    # Update membership view of other membership
                    # ----------------------------------------------------------------
                    # dbConn = model.PyMongoModel()

                    # j = 0
                    # collection_server = dbConn.getCollection("process_" + str(self.port))
                    # doc_server = self.collection.find_one()
                    # for member in doc_server['viewOfMembership']:
                    #     member_port = member['address']
                    #     collection_member = dbConn.getCollection("process_" + str(member_port))
                    #     doc_member = collection_member.find_one()
                    #
                    #     if (member_port != self.port):
                    #         client = client_socket.ClientSocket()
                    #         doc_member = doc_server
                    #
                    #         # doc['viewOfMembership'][j] = member
                    #         # j += 1
                    #         # collection.update({'_id': doc['_id']}, doc)
                    #         print(member)
                    #         client.close()

                    #
                    # client = client_socket.ClientSocket()
                    # # client.sendMessage()
                    # update_mem_view = json.dumps({'topic':'MEMBERSHIP_UPDATE', 'address':args.port})
                    # client.sendMessage(port=self.port, message=update_mem_view.encode('utf-8'));
                    # ----------------------------------------------------------------

                    # Iterate over each member in the list and send a PING request to check
                    # their alive status.
                    # Update membership view accordingly
                    print("\n\nBroadcasting updated membership...")
                    doc = self.collection.find_one()
                    for member in doc['viewOfMembership']:
                        print("Inside the view")
                        member_port = member['address']
                        print("Member port:", member_port)
                        print("Coordinator port:", self.port)

                        if (member_port != self.port):
                            print("not self port ",self.port)
                            client = client_socket.ClientSocket()
                            # alive_status_msg = {'topic': 'PING'}
                            updatedview = json.dumps({'topic':'MEMBERSHIP_UPDATE', 'message':{'viewOfMembership': doc['viewOfMembership']}}).encode('utf-8')
                            print("-----",updatedview)
                            isSuccessSend = client.sendMessage(port=member_port,
                                                               message= updatedview)
                            client.close()
                        print(isSuccessSend)

                        print(member)
                    clientsocket.send((json.dumps({"topic": 'APPROVED', "key": key}))
                                          .encode('utf-8'))





                # check type of message received and perform corressponding action
                elif topic == 'MEMBERSHIP_UPDATE':
                    print("----Inside Membership update")
                    # mem_view_msg = json.dumps({'topic': 'MEMBERSHIP_UPDATE', 'message'})
                    # client = client_socket.ClientSocket()
                    # client.sendMessage(port=args.coordinatorPort, message=mem_view_msg.encode('utf-8'));
                    print("Updated recieved:" ,recvd_msg['message']['viewOfMembership'])
                    print("printing ",self.collection.find_one())
                    # doc = self.collection.find_one()
                    print ("----",doc['viewOfMembership'])
                    # if doc is not None:
                    #     self.collection.delete_one({"_id": doc["_id"]});

                    doc['viewOfMembership'] = recvd_msg['message']['viewOfMembership']
                    print("jhadsgfjaksdh",doc['viewOfMembership'])

                    utils.insertIfNotPresent(self.collection, doc)
                    # client.close()


                elif topic == 'GIVE_MEMBERSHIP_VIEW':
                    # query for membership view
                    doc = self.collection.find_one()

                    # send membership view
                    clientsocket.send((json.dumps({'viewOfMembership':doc['viewOfMembership']}))
                    .encode('utf-8'))
                    
                
                       
            except Exception as ex:
                traceback.print_tb(ex.__traceback__)
                print("ERROR: Exception caught on server")
                
            finally:
                clientsocket.close()
                
                    
