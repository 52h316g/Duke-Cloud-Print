//
//  python_scripts_interface.c
//  libjingle_examples
//
//  Created by Jason on 7/18/14.
//
//

#include <fstream>
#include "python_scripts_interface.h"

std::string getAccessToken() {
    //    Py_Initialize();
    FILE *fp = fopen((script_dir + "get_access_token.py").c_str(), "r");
    PyRun_SimpleFile(fp, (script_dir + "get_access_token.py").c_str());
    //    Py_Finalize();
    
    std::ifstream myfile;
    myfile.open ((script_dir + "access_token_only.txt").c_str());
    std::string auth_token;
    myfile >> auth_token;
    myfile.close();
    return auth_token;
}

void processJobs() {
    FILE *fp = fopen((script_dir + "process_jobs.py").c_str(), "r");
    PyRun_SimpleFile(fp, (script_dir + "process_jobs.py").c_str());
}
