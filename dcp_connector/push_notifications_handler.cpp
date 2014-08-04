//
//  push_notification_handler.cpp
//  libjingle_examples
//
//  Created by Jason on 7/18/14.
//
//

#include "push_notifications_handler.h"

PushNotificationsHandler::~PushNotificationsHandler() {
    delete subscribeTask;
    delete listenTask;
}

void PushNotificationsHandler::setPump(buzz::XmppPump * pump) {
    client = pump->client();
    notifier::SubscriptionList subscriptionList(1);
    notifier::Subscription subscription;
    subscription.channel = "cloudprint.google.com";
    subscription.from = "cloudprint.google.com";
    subscriptionList[0] = subscription;
    subscribeTask = new notifier::PushNotificationsSubscribeTask(client, subscriptionList);
    listenTask = new notifier::PushNotificationsListenTask(client);
}

void PushNotificationsHandler::OnStateChange(buzz::XmppEngine::State state) {
    switch (state) {
        case buzz::XmppEngine::STATE_START:
            std::cout<< "STATE_START\n";
            // Attempting sign in.
            break;
        case buzz::XmppEngine::STATE_OPENING:
            std::cout<< "STATE_OPENING\n";
            // Negotiating with server.
            break;
        case buzz::XmppEngine::STATE_OPEN:
            // Connection succeeded. Send your presence information.
            // and sign up to receive presence notifications.
            std::cout<< "STATE_OPEN\n";
            OnSignon();
            break;
        case buzz::XmppEngine::STATE_CLOSED:
            std::cout<< "STATE_CLOSED\n";
            // Connection ended.
            break;
        case buzz::XmppEngine::STATE_NONE:
            std::cout<< "STATE_NONE\n";
            break;
    }
}

void PushNotificationsHandler::OnSignon() {
    subscribeTask->Start();
    listenTask->Start();
}
