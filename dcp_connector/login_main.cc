/*
 * libjingle
 * Copyright 2004--2005, Google Inc.
 *
 * Redistribution and use in source and binary forms, with or without 
 * modification, are permitted provided that the following conditions are met:
 *
 *  1. Redistributions of source code must retain the above copyright notice, 
 *     this list of conditions and the following disclaimer.
 *  2. Redistributions in binary form must reproduce the above copyright notice,
 *     this list of conditions and the following disclaimer in the documentation
 *     and/or other materials provided with the distribution.
 *  3. The name of the author may not be used to endorse or promote products 
 *     derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
 * EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>
#include <iostream>

#include "talk/base/thread.h"
#include "talk/xmpp/xmpppump.h"
#include "talk/xmpp/constants.h"
#include "talk/xmpp/xmppclientsettings.h"
#include "talk/xmpp/xmppengine.h"
#include "talk/xmpp/xmppclient.h"
#include "talk/xmpp/xmppsocket.h"
#include "talk/base/ssladapter.h"
#include "talk/xmpp/xmppauth.h"
#include "push_notifications_handler.h"
#include "python_scripts_interface.h"

int main(int argc, char **argv) {
    
    // Initialize SSL channel.
//    talk_base::InitializeSSL();
    
    // Create the signaling thread.
    // AutoThread captures the current OS thread and sets it to be
    // ThreadManager::CurrentThread, which will be called and used by SessionManager
//    talk_base::PhysicalSocketServer ss;
    Py_Initialize();
    talk_base::Thread *main_thread = talk_base::Thread::Current();
    
    // Get the information we'll need to sign in.
    PushNotificationsHandler pushNotificationsHandler;
    buzz::XmppPump pump(&pushNotificationsHandler);
    pushNotificationsHandler.setPump(&pump);
    buzz::XmppClientSettings xcs;
    
    xcs.set_user("jixin.liao");
//    xcs.set_resource("pcp");  // Arbitrary resource name.
    xcs.set_host("gmail.com");
    xcs.set_auth_token(buzz::AUTH_MECHANISM_OAUTH2,
                       getAccessToken().c_str());
    xcs.set_use_tls(buzz::TLS_DISABLED);
    xcs.set_server(talk_base::SocketAddress("talk.google.com", 5222));

//    pump.client()->SignalStateChange.connect(&tmp, &Temp::OnStateChange);
    pump.DoLogin(xcs, new buzz::XmppSocket(buzz::TLS_DISABLED), new XmppAuth());
    
    // Start the thread and run indefinitely.
    main_thread->Run();
    
    
    // Function that receives sign in progress notifications.
}
