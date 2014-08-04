//
//  python_scripts_interface.h
//  libjingle_examples
//
//  Created by Jason on 7/18/14.
//
//

#ifndef libjingle_examples_python_scripts_interface_h
#define libjingle_examples_python_scripts_interface_h

#include <string>
#include <python2.7/Python.h>

const std::string script_dir = "./dcp_connector/python_scripts/";

std::string getAccessToken();
void processJobs();
#endif
