#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>

#define MAX_LOG_ENTRY_SIZE	1024
char buf[256];

char *loadEntry(){
	char *buf = malloc(MAX_LOG_ENTRY_SIZE * sizeof(char));
	if (buf == NULL){
		perror("malloc failed.");
		exit(1);
	}
	
	char c = getchar(), *p = buf;
	*p++ = '\n';
	while ((c = getchar()) != EOF && (*(p - 1) != '-' || c != ' '))
		*p++ = c;
	
	*(p - 1) = '\0';
	return buf;
}

char *getProperty(char *entry, char *property){
	char *p = strstr(entry, property);
	if (p == NULL) return NULL;
	p = p + strlen(property);
	return strndup(p, strchr(p, '\n') - p);
}

struct tm *str2tm(char *str){
	struct tm *t = malloc(sizeof(struct tm));
	int tzone;
	memset(t, 0, sizeof(struct tm));
	sscanf(pCTime, "%d-%d-%dT%d:%d:%d+%d", &fCTime.tm_year, &fCTime.tm_mon, &fCTime.tm_mday, &fCTime.tm_hour, &fCTime.tm_min, &fCTime.tm_sec, &tzone;)
}

int main(void){
	while (!feof(stdin)){
		char *e = loadEntry();
		char *pName = getProperty(e, "\n  name: ");
		char *pType = getProperty(e, "\n  type: ");
		
		printf("Name is \"%s\"\n", pName);
		printf("Type is \"%s\"\n", pType);
		
		if (!strcmp(pType, "file")){
			pid_t pid = fork();
			if (pid ==0){
				sprintf(buf, "skydrive-cli get \"%s\" > \"%s\"%c", pName, pName, '\0');
				printf("Fetching file %s...\n", pName);
				system(buf);
				exit(0);
			}
		} else if (!strcmp(pType, "folder")){
			struct stat fStat;
			char *pCTime = getProperty(e, "\n  created_time: ");
			
			fStat.st_ctime = 
			free(pCTime);
		}
		//printf("\"%s\"\n", e);
		
		free(e);
		free(pName);
		free(pType);
	}
	return 0;
}
