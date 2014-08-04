__author__ = 'Jixin Liao'

import os
import sys
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)
from common import *
import subprocess
from third_party import json2pb, cloud_job_state_pb2

FRONT_END_NAME = 'dcp_register'
os.environ['DJANGO_SETTINGS_MODULE'] = FRONT_END_NAME + '.settings'
sys.path.append(script_dir + '../../' + FRONT_END_NAME)
sys.path.append(script_dir + '../../' + FRONT_END_NAME + '/' + FRONT_END_NAME)

from django.contrib.auth import models
from django.contrib.auth.models import User


def getJobs(printerid=None, jobid=None):
    """Get a list of printer jobs.

    Args:
      printerid: if specified, filter by printer id.
      jobid: if specified, filter by job id.
    Returns:
      dictionary of job id's (key) and printer id's (value).
    """
    keys = ['ownerId', 'ticketUrl', 'fileUrl', 'id']
    jobs = []

    if printerid:
        response = getUrl('%s/fetch?printerid=%s' % (CLOUDPRINT_URL, printerid), [])
    elif jobid:
        response = getUrl('%s/fetch?jobid=%s' % (CLOUDPRINT_URL, jobid), [])
    else:
        response = getUrl('%s/jobs' % CLOUDPRINT_URL)

    response_dict = convertJson(response)
    if response_dict['success']:
        jobs_raw = response_dict['jobs']
        # filter out the useful information
        for job in jobs_raw:
            job_temp = {}
            for key in keys:
                job_temp[key] = job[key]
            jobs.append(job_temp)
    return jobs


def getNetID(ownerId):
    """
    :param ownerId: Google account id
    :return:The Duke netID corresponding to ownerId
    """
    u = User.objects.get(email=ownerId)
    if u.is_active:
        return u.username
    else:
        raise User.DoesNotExist


def updateJobState(jobId, jobState):
    printJobStateDiff = cloud_job_state_pb2.PrintJobStateDiff()
    printJobStateDiff.state.type = jobState
    if jobState == cloud_job_state_pb2.JobState.ABORTED:
        printJobStateDiff.state.service_action_cause.error_code = cloud_job_state_pb2.JobState.ServiceActionCause.OTHER
    msg = json2pb.json_encode(printJobStateDiff)
    params = {
        'jobid': jobId,
        'semantic_state_diff': msg
    }
    response = callAPI('control', params)
    print 'update job status success? ' + str(response['success']) + '\nupdate job status message: ' + response[
        'message']


def doJob(job):
    try:
        netId = getNetID(job['ownerId'])
    except User.DoesNotExist:
        updateJobState(job['id'], cloud_job_state_pb2.JobState.ABORTED)
        logger.error('Unauthorized print request from: '+job['ownerId'])
        return

    params = {
        'jobid': job['id'],
        'use_cjt': 'true'
    }
    fileName = script_dir + 'pdf_files/' + str(time.time()) + '.pdf'
    writeFile(fileName, getUrl(job['fileUrl'], []))
    ticket = callAPI('ticket', params)
    # p = subprocess.Popen(["ls", "-l", "/etc/resolv.conf"], stdout=subprocess.PIPE)
    # output, err = p.communicate()
    # print "*** Running ls -l command ***\n", output
    subprocess.call(['lpr', '-P', 'ePrint-OIT', '-U', netId, fileName])
    print "Printing for user: " + netId
    updateJobState(job['id'], cloud_job_state_pb2.JobState.DONE)


def processJobs():
    jobs = getJobs(printerid=PRINTER_ID)
    for job in jobs:
        doJob(job)

processJobs()
# getNetID('2')
