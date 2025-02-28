"""
University of Waterloo Fall 2023 ECE-358 LAB-2  Group 151
József IVÁN GAFO (21111635) jivangaf@uwaterloo.ca
Sonia NAVAS RUTETE (21111397) srutete@uwaterloo.ca
V 1:0
Description: In this module we will write the code for the client for the task 2 of lab 2
"""
#imports
import random
from socket import *

#Create class
class Client:
    def __init__(self,server_ip:str,server_port:int) -> None:
        self.__server_ip=server_ip
        self.__server_port=server_port
        self.__client_socket=socket(AF_INET, SOCK_DGRAM)

    def initialize(self):
        """
        We initialize the request to the dns server
        """
        while True:
            print("Input from the user:")
            domain=input("Enter Domain Name: ")
            domain=domain.lower()

            #We finish connection if input is end
            if domain=="end":
                self.__client_socket.close()
                print("Session Ended")
                break

            #We create the structure of the dns request
            dns_header=self.__dns_header()
            dns_query=self.__dns_query(domain)
            dns_request=dns_header+dns_query

            #Send request to the server
            self.__client_socket.sendto(dns_request,(self.__server_ip,self.__server_port))
            response, addr = self.__client_socket.recvfrom(2048)
            print("Output:")
            response_dict=self.__extract_data(response.hex())

            #If there are no errors
            self.print_response(response_dict)
            print("")

    
    #Functions to create the request headers + data
    def __dns_header(self)->bytes:
        """
        This method is in charge of generating the header of the dns
        """
        #We generate the ID
        random_id=random.randint(0,(2**16)-1)
        dns_id=self.int_to_bytes(random_id,2)

        #We generate the flag header
        flags = self.generate_flags()

        #We generate the other headers
        qdcount=self.int_to_bytes(1,2)#number of entries in question section

        #Based on message type
        ancount=self.int_to_bytes(0,2)#number of resource records in answer section

        nscount=self.int_to_bytes(0,2)#number of name server resource records in authorative records
        arcount=self.int_to_bytes(0,2)#number of resource records additional record section

        return dns_id+flags+qdcount+ancount+nscount+arcount

    def __dns_query(self,domain:str)->bytes:
        """
        This method is in charge of generating the dns query
        """
        #Revise qname to bytes
        labels = domain.split(".")
        qname = b"" # Initialize
        for label in labels:
            qname += self.int_to_bytes(len(label),1)
            qname += label.encode()
        qname += self.int_to_bytes(0,1) # End of domain

        qtype=self.int_to_bytes(1,2)
        qclass=self.int_to_bytes(1,2)

        return qname+qtype+qclass
    
    def generate_flags(self):
        """
        We generate the flag header
        """
        qr = "0"  # 0 is query, 1 is response
        opcode = "0000"  # Standard query
        aa = "1"    # Authoritative answer
        tc = "0"    #Message truncated
        rd = "0"    #recursion desired
        ra = "0"    #recursion avaible
        z = "000"   #for future use
        rcode ="0000"  #Response code

        flags=qr+opcode+aa+tc+rd+ra+z+rcode

        #We convert it to bytes and we return it
        return self.bits_to_bytes(flags)

    def __extract_data(self,hex_data:hex)->dict:
        """
        Method of extracting the data from the server
        @hex_data: All the data of the response in hex
        @return dict: It return a dictionary with all the fields
        """
        #General data of the response
        data={
            "id_req":hex_data[:4],
            "flags_req":hex_data[4:8],
            "qdcount":hex_data[8:12],
            "ancount":hex_data[12:16],
            "nscount":hex_data[16:20],
            "arcount":hex_data[20:24],
            "question":[],
            "answers":[]
        }
        i=24
        #We extract the query data
        qdcount=int(data["qdcount"],16)
        for _ in range(qdcount):
            domain,qtype,qclass,i=self.__extract_query(hex_data,i)
            data["question"].append({
                "qname":domain,
                "qtype":qtype,
                "qclass":qclass
            })
        #We skip 8 hex that are the qsection(owner name)
        # We extract the answer section
        i+=8
        #Now we iterate as many responses we have
        ancount=int(data["ancount"], 16)
        for _ in range(ancount):
            anname,answer_type, answer_class, answer_ttl, rd_length, rd_data, i = self.__extract_answer_section(hex_data, i)
            data["answers"].append({
                "anname":anname,
                "answer_type": answer_type,
                "answer_class": answer_class,
                "answer_ttl": answer_ttl,
                "rd_length": rd_length,
                "rd_data": rd_data,
        })
        return data
    

    def __extract_query(self, hex_data: hex, i: int) -> [str, hex, hex, int]:
        """
        This method is in charge of finding the fields of the query
        @hex_data: the response in hex
        @i: integer that represents the position in hex_data
        @return: returns the domain, qtype, qclass, and the position in hex_data
        """

        #obtain the first part of the domain length (*2 because they are hex not bytes)
        length_first_part=self.hex_to_int(hex_data[i:i+2])*2
        i+=2
        first_domain=self.hex_to_str(hex_data[i:i+length_first_part])
        i+=length_first_part

        #We obtain the second part (*2 because they are hex not bytes)
        length_second_part=self.hex_to_int(hex_data[i:i+2])*2
        i+=2
        second_domain=self.hex_to_str(hex_data[i:i+length_second_part])
        i+=length_second_part
        
        #We create the domain
        domain=first_domain+"."+second_domain
                                      

        # Skip over the null terminator
        i += 2

        return domain, hex_data[i:i+2], hex_data[i+2:i+4],i
    

    def __extract_answer_section(self, hex_data, i):
        """
        Extracts the answer section from the response in hex.
        @param hex_data: Hex data of the response.
        @param i: Position in hex_data.
        @return: Owner name, type, class, TTL, RDLength, RData, and updated position in hex_data.
        """
        #get anname
        anname=hex_data[i:i+4]
        i+=4

        #get answer type
        answer_type = hex_data[i:i+4]
        i += 4

        #GEt answer type
        answer_class = hex_data[i:i+4]
        i += 4

        #Get answer ttl 
        answer_ttl = hex_data[i:i+8]
        i += 8

        #get rdlength
        rd_length = hex_data[i:i+4]
        i += 4

        hex_data_length=self.hex_to_int(rd_length)*2#*2 because they are bytes

        rd_data = hex_data[i:i + hex_data_length]
        i += hex_data_length

        return anname,answer_type, answer_class, answer_ttl, rd_length, rd_data, i


    #Methods to print the output
    def print_response(self,response:dict)->None:
        """
        Method to print the response from the server
        @response: Is a dictionary containing the answer of the server 
        """
        #Check if we don't have any errors
        if response["flags_req"][2:]=="03":
            domain=response["question"][0]["qname"]
            print(f"[ERROR]: the DNS {domain} was not found")
        line=""

        #We obtain the domain from all the data extracted
        domain=response["question"][0]["qname"]

        answer_list=response["answers"]
        for answer in answer_list:
            #We create the print message
            line=">"
            line+=domain+": "

            #Get answer type
            if self.hex_to_int(answer["answer_type"])==1:
                line+="Type: A, "
            else:
                #For the moment we only accept type A answers
                raise ValueError("[ERROR]: We only accept type A")
            
            #get class
            if self.hex_to_int(answer["answer_class"])==1:
                line+="Class: IN, "
            else:
                raise ValueError("[ERROR]: We only accept IN")

            #get ttl
            line+="TTL: "+str(self.hex_to_int(answer["answer_ttl"]))+", "

            #get rdlength
            rdlength=self.hex_to_int(answer["rd_length"])

            if rdlength==4:
                line+="addr ("+str(rdlength)+") "
            else:
                raise ValueError("[ERROR] The client only support ipv4")

            #Get ip
            ipv4=self.hex_to_ipv4(answer["rd_data"])
            line+=ipv4
            #Print the answer
            print(line)

    #static methods
    @staticmethod
    def int_to_bytes(number:int,byte_size:int)->bytes:
        """
        Method to convert an integer to bytes
        @number: The number we want to convert into bytes
        @byte_size: How many bytes do we want to generate
        @return bytes: we return the conversion of number into bytes
        """
        #Byteorder big= most significant byte comes first
        return number.to_bytes(byte_size,byteorder="big")
    
    @staticmethod
    def bits_to_bytes(bits:str)->bytes:
        """
        Method in charge of translating bits into bytes
        @bits: A string containing bits
        @return bytes: We return the conversion of bits to bytes
        """
        if len(bits)%8!=0:
            raise ValueError("[Error] The bit length must be multiple of 8")
        
        #We divide the bits by chunks of 8
        byte_chunks=[bits[i:i+8] for i in range(0, len(bits), 8)]

        result_in_bytes = bytes([int(chunk, 2) for chunk in byte_chunks])
        return result_in_bytes

    @staticmethod
    def hex_to_str(hex_data:hex)->str:
        """
        Method to convert a hexadecimal into a string
        @hex_data: hexadecimal numbers that contain a string
        @return str: return te conversion from hex to string
        """

        return bytes.fromhex(hex_data).decode('utf-8')
    
    @staticmethod
    def hex_to_int(hex_data:hex)->int:
        """
        Convert a hexadecimal number to an integer
        @hex_data: hexadecimal numbers that contain an integer
        @return str: return te conversion from hex to in
        """
        return int(hex_data,16)

    @staticmethod
    def hex_to_ipv4(hex_data:hex)->str:
        """
        Convert an hexadecimal into ipv4
        @hex_data: hexadecimal number that we want to convert into ip
        @return: It returns a string containing the ipv4
        """
        ipv4_address = ""
        aux = 0
        for i in range(4):
            ipv4_part = str(int(hex_data[aux:aux+2], 16))
            ipv4_address += ipv4_part
            if i != 3:
                ipv4_address += "."
            aux += 2
            
        return ipv4_address
   


if __name__=="__main__":
    serverIP="127.0.0.1"
    serverPort=12000
    client=Client(serverIP,serverPort)
    client.initialize()