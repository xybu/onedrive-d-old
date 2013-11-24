#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/inotify.h>

#define EVENT_SIZE	( sizeof (struct inotify_event) )
#define BUF_LEN		 ( 1024 * ( EVENT_SIZE + 16 ) )
#define READ_BUFFER	1024

int main(int argc, char* argv[]){
	int length, i = 0;
	int fd;
	int wd;
	int iBuffer = 0;
	char buffer[BUF_LEN];
	char rBuffer[READ_BUFFER];
	char *SkyDrive_Dir = NULL, *homePath, *sConfPath;
	FILE *sConf;
	
	homePath = getenv("HOME");	//in stdlib.h
	iBuffer = sprintf(rBuffer, "%s", homePath);
	sprintf(rBuffer + iBuffer, "%s%c", "/.skydrive/user.conf", '\0');
	sConfPath = strdup(rBuffer);
	if ((sConf = fopen(rBuffer, "r")) == NULL) perror("Error opening user.conf.");
	else {
		if (fgets(rBuffer, READ_BUFFER, sConf) == NULL) perror("fgets");
		else puts(rBuffer);
		
		if (fgets(rBuffer, READ_BUFFER, sConf) == NULL) perror("fgets2");
		
		char *rEqualSign = strchr(rBuffer, '=');
		SkyDrive_Dir = strndup(rEqualSign + 1, strlen(rEqualSign) - 2);
		printf("The dir is \"%s\".\n", SkyDrive_Dir);
		//exit(0);
		fclose(sConf);
	}

	if ((fd = inotify_init()) < 0) perror("Error occured doing inotify_init.");
	
	wd = inotify_add_watch(fd, SkyDrive_Dir, IN_ATTRIB | IN_MODIFY | IN_CREATE | IN_DELETE | IN_MOVED_FROM | IN_MOVED_TO);
	
	length = read(fd, buffer, BUF_LEN);

	if (length < 0) perror("read");	

	while ( i < length ) {
		//if (i >= length) continue;
		struct inotify_event *event = ( struct inotify_event * ) &buffer[ i ];
		if ( event->len ) {
			if ( event->mask & IN_CREATE ) {
				if ( event->mask & IN_ISDIR ) {
					printf( "The directory %s was created.\n", event->name );			 
				} else {
					printf( "The file %s was created.\n", event->name );
				}
			} else if ( event->mask & IN_DELETE ) {
				if ( event->mask & IN_ISDIR ) {
					printf( "The directory %s was deleted.\n", event->name );			 
				}
				else {
					printf( "The file %s was deleted.\n", event->name );
				}
			} else if ( event->mask & IN_MODIFY ) {
				if ( event->mask & IN_ISDIR ) {
					printf( "The directory %s was modified.\n", event->name );
				} else {
					printf( "The file %s was modified.\n", event->name );
				}
			}
		}
		i += EVENT_SIZE + event->len;
		//length += read(fd, buffer, BUF_LEN);
	}

	inotify_rm_watch( fd, wd );
	close( fd );
	
	free(SkyDrive_Dir);
	free(sConfPath);
	return 0;
}
