/* Using Inotify to monitor the sub-dirs under the specifiied dir*/
 
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/inotify.h>
#include <dirent.h>
#include <limits.h>
 
#define MAX_LEN 1024 /*Path length for a directory*/
#define MAX_EVENTS 1024 /*Max. number of events to process at one go*/
#define LEN_NAME 16 /*Assuming that the length of the filename won't exceed 16 bytes*/
#define EVENT_SIZE  ( sizeof (struct inotify_event) ) /*size of one event*/
#define BUF_LEN     ( MAX_EVENTS * ( EVENT_SIZE + LEN_NAME )) /*buffer to store the data of events*/
 
 
/* Log file*/
FILE *fp_log;
  
 
/* Add inotify watches to directories immediately under root
 * in addition to itself */
 
void add_watches(int fd, char *root)
{
  int wd;
  char *abs_dir;
  struct dirent *entry;
  DIR *dp;
 
  dp = opendir(root);
  if (dp == NULL)
    {
      perror("Error opening the starting directory");
      exit(0);
    }
 
  /* add watch to starting directory */
  wd = inotify_add_watch(fd, root, IN_CREATE | IN_MODIFY | IN_DELETE);
  if (wd == -1)
    {
      fprintf(fp_log,"Couldn't add watch to %s\n",root);
    }
  else
    {
      printf("Watching:: %s\n",root);
    }
 
  /* Add watches to the Level 1 sub-dirs*/
  abs_dir = (char *)malloc(MAX_LEN);
  while((entry = readdir(dp)))
    {
      /* if its a directory, add a watch*/
      if (entry->d_type == DT_DIR)
        {
          strcpy(abs_dir,root);
          strcat(abs_dir,entry->d_name);
           
          wd = inotify_add_watch(fd, abs_dir, IN_CREATE | IN_MODIFY | IN_DELETE);
          if (wd == -1)
              printf("Couldn't add watch to the directory %s\n",abs_dir);
          else
            printf("Watching:: %s\n",abs_dir);
        }
    }
   
  closedir(dp);
  free(abs_dir);
}
 
/* Main routine*/
int main( int argc, char **argv )
{
  int length, i = 0;
  int fd;
  char buffer[BUF_LEN], root[MAX_LEN];
 
 
  /*Check for supplied path to monitor*/
  switch(argc)
    {
    case 1: printf("No directory specified. Will monitor the entire filesystem...\n\n");
      strcpy(root,"/");
      break;
       
    case 2: strcpy(root,argv[1]);
      if(root[strlen(root)-1]!='/')
        strcat(root,"/");
      puts(root);
 
      break;
       
    default: printf("Ignoring all other arguments after the first\n");
    }
   
 
  /* Set up logger*/
  fp_log = fopen("inotify_logger.log","a");
  if (fp_log == NULL)
    {
      printf("Error opening logger. All output will be redirected to the stdout\n");
      fp_log = stdout;
    }
 
  fd = inotify_init();
  if ( fd < 0 ) {
    perror( "Couldn't initialize inotify");
  }
 
  /* Read the sub-directories at one level under argv[1]
   * and monitor them for access */
  add_watches(fd,root);
   
  /* do it forever*/
  while(1)
    {
      i = 0;
      length = read( fd, buffer, BUF_LEN ); 
 
      if ( length < 0 ) {
        perror( "read" );
      } 
 
      /* Read the events*/
      while ( i < length ) {
        struct inotify_event *event = ( struct inotify_event * ) &buffer[ i ];
        if ( event->len ) {
          if ( event->mask & IN_CREATE) {
            if (event->mask & IN_ISDIR)
              fprintf(fp_log,"%d DIR::%s CREATED\n", event->wd,event->name );      
            else
              fprintf(fp_log, "%d FILE::%s CREATED\n", event->wd, event->name);      
          }
           
          if ( event->mask & IN_MODIFY) {
            if (event->mask & IN_ISDIR)
              fprintf(fp_log,"%d DIR::%s MODIFIED\n", event->wd,event->name );      
            else
              fprintf(fp_log,"%d FILE::%s MODIFIED\n", event->wd,event->name );      
 
          }
           
          if ( event->mask & IN_DELETE) {
            if (event->mask & IN_ISDIR)
              fprintf(fp_log,"%d DIR::%s DELETED\n", event->wd,event->name );      
            else
              fprintf(fp_log,"%d FILE::%s DELETED\n", event->wd,event->name );      
          } 
 
          i += EVENT_SIZE + event->len;
        }
      }
    }
  /* Clean up*/
  ( void ) close( fd );
   
  return 0;
}
