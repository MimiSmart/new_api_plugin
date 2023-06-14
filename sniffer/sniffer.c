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

static PyObject* main(PyObject* pSelf, PyObject* pArgs, PyObject* pKywdArgs){
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

    unsigned char *buffer = (unsigned char *) malloc(65536); //Its Big!
    int sock_raw = socket( AF_PACKET , SOCK_RAW , htons(ETH_P_ALL)) ;

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
        //Now process the packet
        
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

        char* ip_hdr = malloc(iphdrlen);
        char* udp_hdr = malloc(sizeof udph);
        char* data_payload = malloc(data_size - header_size);
        strncpy(ip_hdr,buffer,iphdrlen);
        strncpy(udp_hdr, buffer+iphdrlen, sizeof udph);
        strncpy(data_payload, buffer + header_size, data_size - header_size);

        PyObject* pArgs2 = Py_BuildValue(
            "({s:[i,i,i,i,i,i], s:[i,i,i,i,i,i], s:H, s:I, s:I, s:I, s:I, s:I,s:I, s:I, s:I, s:s, s:s, s:I, s:I, s:I, s:I, s:y, s:y, s:y})",

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
            "ip_src_addr",          inet_ntoa(source.sin_addr),
            "ip_dest_addr",         inet_ntoa(dest.sin_addr),

            "udp_src_port",         ntohs(udph->source),
            "udp_dest_port",        ntohs(udph->dest),
            "udp_len",              ntohs(udph->len),
            "udp_checksum",         ntohs(udph->check),

            "ip_hdr",                ip_hdr,
            "udp_hdr",               udp_hdr,
            "data_payload",          data_payload
            );

    // invoke the callback
        PyObject* pKywdArgs2 = NULL ;
        PyObject* pResult = PyObject_Call( pCallback, pArgs2, pKywdArgs2 ) ;

        Py_DECREF( pArgs2 ) ;
        Py_XDECREF( pKywdArgs2 ) ;
        Py_DECREF( pResult ) ;

        free(ip_hdr);
        free(udp_hdr);
        free(data_payload);
    }
    close(sock_raw);
    return Py_BuildValue("i",0);
}

static PyMethodDef mainMethods[] = {
 {"main",(PyCFunction)main,METH_VARARGS|METH_KEYWORDS,"Sniff UDP packets"},
 {NULL,NULL,0,NULL}
};

static PyModuleDef sniffer = {
 PyModuleDef_HEAD_INIT,
 "sniffer","Sniff UDP packets",
 -1,
 mainMethods
};

PyMODINIT_FUNC PyInit_sniffer(void){
 return PyModule_Create(&sniffer);
}
