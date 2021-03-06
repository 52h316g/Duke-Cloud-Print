__author__ = 'Jixin Liao'

import os
import sys
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)
from common import *
import subprocess
from third_party import json2pb, cloud_job_state_pb2

from django.contrib.auth import models
from django.contrib.auth.models import User

import unicodedata

def getJobs(printerid=None, jobid=None):
    """Get a list of printer jobs.

    Args:
      printerid: if specified, filter by printer id.
      jobid: if specified, filter by job id.
    Returns:
      dictionary of job id's (key) and printer id's (value).
    """
    keys = ['ownerId', 'ticketUrl', 'fileUrl', 'id', 'title']
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
        # filter out the useful information and convert unicode to strings
        for job in jobs_raw:
            job_temp = {}
            for key in keys:
                job_temp[key] = unicodedata.normalize('NFKD', job[key]).encode('ascii', 'ignore')
            jobs.append(job_temp)
    return jobs


def getNetID(ownerId):
    """
    :param ownerId: Google account id
    :return: Duke NetID corresponding to ownerId
    """
    u = User.objects.get(email__iexact=ownerId)
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


def genFileName(_title):
    keepCharacters = (' ', '.', '_')
    title = "".join(c for c in _title if c.isalnum() or c in keepCharacters).rstrip()
    return script_dir + 'pdf_files/' + title + '.pdf'


def doJob(job):
    try:
        netId = getNetID(job['ownerId'])
    except User.DoesNotExist:
        updateJobState(job['id'], cloud_job_state_pb2.JobState.ABORTED)
        logger.error('Unauthorized print request from: '+job['ownerId'])
        return
    fileName = genFileName(job['title'])
    writeFile(fileName, getUrl(job['fileUrl'], []))
    params = {
        'jobid': job['id'],
        'use_cjt': 'true'
    }
    ticket = callAPI('ticket', params)['print']
    command = ['lpr', '-P', 'ePrint-OIT', '-U', netId, '-o', 'fit-to-page']
    if 'copies' in ticket:
        command.append('-#' + str(ticket['copies']['copies']))
    if 'duplex' in ticket:
        if ticket['duplex']['type'] == 'LONG_EDGE':
            command.extend(['-o', 'sides=two-sided-long-edge'])
        elif ticket['duplex']['type'] == 'SHORT_EDGE':
            command.extend(['-o', 'sides=two-sided-short-edge'])
    # if 'page_orientation' in ticket:
    #     if ticket['page_orientation']['type'] == 'LANDSCAPE':
    #         command.extend(['-o', 'landscape'])
    command.append(fileName)
    subprocess.call(command)
    print "Printing for user: " + netId
    print "Document title: " + job['title']
    subprocess.call(['rm', fileName])
    updateJobState(job['id'], cloud_job_state_pb2.JobState.DONE)


def processJobs():
    jobs = getJobs(printerid=PRINTER_ID)
    for job in jobs:
        doJob(job)

processJobs()
# getNetID('2')
