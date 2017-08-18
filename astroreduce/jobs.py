# BSD 3-Clause License
#
# Copyright (c) 2017, Zackary Parsons
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import multiprocessing
from queue import Queue
from threading import Thread
from time import sleep
from typing import Callable, Tuple

_job_queue = Queue()                     # FIFO job queue
_cpu_count = multiprocessing.cpu_count() # Max threads = _cpu_count

class Job:
    target = None     # Function to call when running in thread
    args = None       # Arguments to pass to function
    return_val = None # Return value of the target
    has_run = False   # True if the job has been run

    def run(self):
        self.return_val = self.target(*self.args)
        self.has_run = True
        return self.return_val

    def __init__(self, target: Callable, args: Tuple = ()):
        self.target=target
        self.args=args


def _job_worker():
    while not _job_queue.empty():
        job = _job_queue.get()
        job.run()
        _job_queue.task_done()


def push_job(new_job: Job):
    """ Push a new job into the FIFO queue """
    _job_queue.put(new_job)


def start_jobs(max_threads: int = 0):
    """ Start running the jobs in the job queue """
    global _cpu_count
    if max_threads <= 0:
        max_threads = _cpu_count

    for i in range(max_threads):
        t = Thread(target=_job_worker)
        t.daemon = True
        t.start()


def wait_done():
    """ Wait until all jobs have finished running """
    _job_queue.join()
