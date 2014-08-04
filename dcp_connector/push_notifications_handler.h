//
//  push_notification_handler.h
//  libjingle_examples
//
//  Created by Jason on 7/18/14.
//
//

#ifndef __libjingle_examples__push_notification_handler__
#define __libjingle_examples__push_notification_handler__

#include <iostream>
//#include "talk/base/thread.h"
#include "talk/xmpp/xmpppump.h"
//#include "talk/xmpp/constants.h"
//#include "talk/xmpp/xmppclientsettings.h"
#include "talk/xmpp/xmppengine.h"
//#include "talk/xmpp/xmppclient.h"
//#include "talk/xmpp/xmppsocket.h"
//#include "talk/base/ssladapter.h"
//#include "talk/xmpp/xmppauth.h"
#include "push_notifications_subscribe_task.h"
#include "push_notifications_listen_task.h"

class PushNotificationsHandler: public buzz::XmppPumpNotify, public sigslot::has_slots<> {
public:
    ~PushNotificationsHandler();
    
    void setPump(buzz::XmppPump * pump);
    void OnStateChange(buzz::XmppEngine::State state);
private:
    buzz::XmppClient *client;
    notifier::PushNotificationsSubscribeTask *subscribeTask;
    notifier::PushNotificationsListenTask *listenTask;
    void OnSignon();
};
#endif /* defined(__libjingle_examples__push_notification_handler__) */
