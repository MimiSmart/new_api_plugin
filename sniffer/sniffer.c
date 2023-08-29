#define PY_SSIZE_T_CLEAN
#include <python3.9/Python.h>

#include<netinet/in.h>
#include<errno.h>
#include<netdb.h>
#include<stdio.h> //For standard things
#include<stdlib.h>    //malloc
#include<string.h>    //strlen
 
#include<netinet/ip_icmp.h>   //Provides declarations for icmp header
#include<netinet/udp.h>   //Provides declarations for udp header
#include<netinet/tcp.h>   //Provides declarations for tcp header
#include<netinet/ip.h>    //Provides declarations for ip header
#include<netinet/if_ether.h>  //For ETH_P_ALL
#include<net/ethernet.h>  //For ether_header
#include<sys/socket.h>
#include<arpa/inet.h>
#include<sys/ioctl.h>
#include<sys/time.h>
#include<sys/types.h>
#include<unistd.h>

struct sockaddr_in source,dest;
int i,j;

PyObject* callback_func;

void PrintData (unsigned char* data , int Size);


static PyObject* run(PyObject* pSelf, PyObject* pArgs, PyObject* pKywdArgs){
    //parse args (callback var)
    PyObject* pCallback = NULL ;
    const char* argNames[] = { "callback", NULL } ;
    if ( ! PyArg_ParseTupleAndKeywords( pArgs, pKywdArgs, "O", (char**)argNames, &pCallback ) )
        return NULL ;

    // check that the callback is callable
    if ( pCallback != NULL ) {
        if ( ! PyCallable_Check( pCallback ) ) {
            PyErr_SetString( PyExc_ValueError, "Invalid callback." ) ;
            return NULL ;
        }
    }

    int saddr_size , data_size;
    struct sockaddr saddr;

    unsigned char *buffer = (unsigned char *) malloc(65536);
    int sock_raw = socket( AF_PACKET , SOCK_RAW , htons(ETH_P_ALL)) ;

    //exit if socket is closed
    if(sock_raw < 0){
        perror("Socket Error");
        return Py_BuildValue("i",1);
    }

    while(1){
        saddr_size = sizeof saddr;
        //Receive a packet
        data_size = recvfrom(sock_raw , buffer , 65536 , 0 , &saddr , (socklen_t*)&saddr_size);
        if(data_size <0 ){
            printf("Recvfrom error , failed to get packets\n");
            return Py_BuildValue("i",1);
        }
        //-------------- Get packet data ----------------
        unsigned short iphdrlen;
        struct iphdr *iph = (struct iphdr *)(buffer +  sizeof(struct ethhdr));
        iphdrlen = iph->ihl*4;
        struct udphdr *udph = (struct udphdr*)(buffer + iphdrlen  + sizeof(struct ethhdr));
        int header_size =  sizeof(struct ethhdr) + iphdrlen + sizeof udph;
        struct ethhdr* eth = (struct ethhdr *)buffer;

        memset(&source, 0, sizeof(source));
        source.sin_addr.s_addr = iph->saddr;
        memset(&dest, 0, sizeof(dest));
        dest.sin_addr.s_addr = iph->daddr;

        char* ip_hdr = malloc(iphdrlen*2);
        char* udp_hdr = malloc(sizeof udph);
        char* data_payload = malloc(data_size - header_size);
        for(int i=0;i<iphdrlen;i++)
            ip_hdr[i] = buffer[i];
        for(int i=0;i<sizeof udph;i++)
            udp_hdr[i] = buffer[iphdrlen+i];
        for(int i=0;i<data_size - header_size;i++)
            data_payload[i] = buffer[header_size+i];

        char* dest_ip = malloc(20);
        char* src_ip = malloc(20);
        strcpy(dest_ip,inet_ntoa(dest.sin_addr));
        strcpy(src_ip,inet_ntoa(source.sin_addr));
        //---------------------------------------------------------
        //udp packet protocol==17
        if (iph->protocol == 17){
//            printf( "\n\n***********************UDP Packet*************************\n\n");
//            printf( "Ethernet Header\n");
//            printf( "   |-Destination Address : %.2X-%.2X-%.2X-%.2X-%.2X-%.2X \n", eth->h_dest[0] , eth->h_dest[1] , eth->h_dest[2] , eth->h_dest[3] , eth->h_dest[4] , eth->h_dest[5] );
//            printf( "   |-Source Address      : %.2X-%.2X-%.2X-%.2X-%.2X-%.2X \n", eth->h_source[0] , eth->h_source[1] , eth->h_source[2] , eth->h_source[3] , eth->h_source[4] , eth->h_source[5] );
//            printf( "   |-Protocol            : %u \n",(unsigned short)eth->h_proto);
//
//            printf( "\nIP Header\n");
//            printf( "   |-IP Version        : %d\n",(unsigned int)iph->version);
//            printf( "   |-IP Header Length  : %d DWORDS or %d Bytes\n",(unsigned int)iph->ihl,((unsigned int)(iph->ihl))*4);
//            printf( "   |-Type Of Service   : %d\n",(unsigned int)iph->tos);
//            printf( "   |-IP Total Length   : %d  Bytes(Size of Packet)\n",ntohs(iph->tot_len));
//            printf( "   |-Identification    : %d\n",ntohs(iph->id));
//            printf( "   |-TTL      : %d\n",(unsigned int)iph->ttl);
//            printf( "   |-Protocol : %d\n",(unsigned int)iph->protocol);
//            printf( "   |-Checksum : %d\n",ntohs(iph->check));
//            printf( "   |-Source IP        : %s\n",src_ip);
//            printf( "   |-Destination IP   : %s\n",dest_ip);
//
//            printf( "\nUDP Header\n");
//            printf( "   |-Source Port      : %d\n" , ntohs(udph->source));
//            printf( "   |-Destination Port : %d\n" , ntohs(udph->dest));
//            printf( "   |-UDP Length       : %d\n" , ntohs(udph->len));
//            printf( "   |-UDP Checksum     : %d\n" , ntohs(udph->check));
//
//            printf( "\nIP Header\n");
//            PrintData(buffer , iphdrlen);
//            printf( "\nUDP Header\n");
//            PrintData(buffer+iphdrlen , sizeof udph);
//            printf( "\nData Payload\n");
//            PrintData(buffer + header_size , data_size - header_size);
//            printf( "\n###########################################################");

            //build dict for python
            PyObject* pArgs2 = Py_BuildValue(
            "({s:[i,i,i,i,i,i], s:[i,i,i,i,i,i], s:H, s:I, s:I, s:I, s:I, s:I,s:I, s:I, s:I, s:s, s:s, s:I, s:I, s:I, s:I, s:y#, s:y#, s:y#})",

            "eth_dest_addr",        eth->h_dest[0] , eth->h_dest[1] , eth->h_dest[2] , eth->h_dest[3] , eth->h_dest[4] , eth->h_dest[5],
            "eth_src_addr",         eth->h_source[0] , eth->h_source[1] , eth->h_source[2] , eth->h_source[3] , eth->h_source[4] , eth->h_source[5],
            "eth_protocol",         (unsigned short)eth->h_proto,

            "ip_version",           (unsigned int)iph->version,
            "ip_hdr_len",           ((unsigned int)(iph->ihl))*4,
            "ip_tos",               (unsigned int)iph->tos,
            "ip_total_len",         ntohs(iph->tot_len),
            "ip_identification",    ntohs(iph->id),
            "ip_ttl",               (unsigned int)iph->ttl,
            "ip_protocol",          (unsigned int)iph->protocol,
            "ip_checksum",          ntohs(iph->check),
            "ip_src_addr",          src_ip,
            "ip_dest_addr",         dest_ip,

            "udp_src_port",         ntohs(udph->source),
            "udp_dest_port",        ntohs(udph->dest),
            "udp_len",              ntohs(udph->len),
            "udp_checksum",         ntohs(udph->check),

            "ip_hdr",                ip_hdr, iphdrlen,
            "udp_hdr",               udp_hdr, sizeof udph,
            "data_payload",          data_payload, data_size - header_size
            );

            // invoke the callback
            PyObject* pKywdArgs2 = NULL ;
            PyObject* pResult = PyObject_Call( pCallback, pArgs2, pKywdArgs2 ) ;

            // free py objects
            Py_DECREF( pArgs2 ) ;
            Py_XDECREF( pKywdArgs2 ) ;
            Py_DECREF( pResult ) ;
            Py_DECREF(ip_hdr);
        }

        free(ip_hdr);
        free(udp_hdr);
        free(data_payload);

        free(src_ip);
        free(dest_ip);

//        free(buffer);
//        buffer = (unsigned char *) malloc(65536);

    }
    close(sock_raw);
    return Py_BuildValue("i",0);
}

static PyMethodDef snifferMethods[] = {
 {"run",(PyCFunction)run,METH_VARARGS|METH_KEYWORDS,"Sniff UDP packets"},
 {NULL,NULL,0,NULL}
};

static PyModuleDef sniffer = {
 PyModuleDef_HEAD_INIT,
 "sniffer","Sniff UDP packets",
 -1,
 snifferMethods
};

PyMODINIT_FUNC PyInit_sniffer(void){
 return PyModule_Create(&sniffer);
}


//for debug
void PrintData (unsigned char* data , int Size){
    int i , j;
    for(i=0 ; i < Size ; i++){
        if( i!=0 && i%16==0) {  //if one line of hex printing is complete...
            printf( "         ");
            for(j=i-16 ; j<i ; j++){
                if(data[j]>=32 && data[j]<=128)
                    printf( "%c",(unsigned char)data[j]); //if its a number or alphabet
                 
                else printf( "."); //otherwise print a dot
            }
            printf( "\n");
        } 
         
        if(i%16==0) printf( "   ");
            printf( " %02X",(unsigned int)data[i]);
                 
        if( i==Size-1){  //print the last spaces
            for(j=0;j<15-i%16;j++){
              printf( "   "); //extra spaces
            }
             
            printf( "         ");
             
            for(j=i-i%16 ; j<=i ; j++){
                if(data[j]>=32 && data[j]<=128)
                  printf( "%c",(unsigned char)data[j]);
                else printf( ".");
            }
             
            printf(  "\n" );
        }
    }
}