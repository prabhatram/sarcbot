# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []

from typing import Any, Text, Dict, List

from rasa_sdk import Tracker, Action, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, ConversationPaused, UserUtteranceReverted

import sqlite3


class ActionDefaultAskAffirmation(Action):
    def name(self) -> Text:
        return "action_default_ask_affirmation"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict[Text, Any]
    ):
        # top three intents selected
        predicted_intents = tracker.latest_message["intent_ranking"][1:4]
        
        # Convert technical intent names to natural everyday langauge
        intent_mappings = {"my_order": "Track order",
                           "affirm": "Agree",
                           "deny": "Never mind",
                           "goodbye": "Goodbye",
                           "tell_me_a_joke": "Tell a joke"
                           }
        
        # show the top three intents as buttons for user's convenience
        
        buttons = [
            {
                "title": intent_mappings[intent['name']],
                "payload": "/{}".format(intent['name'])
            }
            for intent in predicted_intents
        ]
        
        # buttons = [{"title": intent_mappings[intent['name']],"payload": "/{}".format(intent['name'])}
        
        # add one more button "None of these", if the user does not agree with any of the above options
        buttons.append({
            "title": "None of these",
            "payload": "/out_of_scope"
        })
        
        #Chatbot asks the user to confirm by selecting one of the optinos
        message = "Well, you confuse me. As expected. Care to be clearer by picking from one of the following?"
        
        dispatcher.utter_message(text=message, buttons=buttons)
        return []

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_default_fallback"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        
        message = "Sorry, I'm not as wise as you. Only another wise guy can help you. \nBe patient while I connect you to that wise guy..."
        dispatcher.utter_message(text=message)
        return [ConversationPaused(), UserUtteranceReverted()]
        # dispatcher.utter_message(template="my_custom_fallback_template")
        # return [UserUtteranceReverted()]


class ActionResetOrderNumber(Action):
    def name(self) -> Text:
        return "action_reset_order_number"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        return [SlotSet("order_number", None)]


class ValidateSimpleOrderForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_simple_order_form"

    def validate_order_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        
        # If the name is super short, it might be wrong.
        global order 
        order = slot_value
        print(f"Order number = {order} length = {len(order)}")
        if len(order) == 0:
            dispatcher.utter_message(text="Shouldn't your order number be made of actual order number?")
            return {"order_number": None}
        elif len(order) < 4:
            dispatcher.utter_message(text="That order number is way too short. How about you provide me a 4-character order number?")
            return {"order_number": None}
        elif len(order) > 4:
            dispatcher.utter_message(text="That order number is way too long. How about you provide me a 4-character order number?")
            return {"order_number": None}
        
        return {"order_number": order}
    

class QueryOrderDetails(Action):

    def name(self) -> Text:
        return "query_order_details"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Runs a query using only the order ID column, outputs an utterance 
        to the user w/ the relevent 
        information for one of the returned rows.
        """
        conn = DbQueryingMethods.create_connection(db_file="sarcdb/SarcbotDB.db")

        # slot_value = tracker.get_slot("order_number")

        get_query_results = DbQueryingMethods.select_by_slot(conn=conn,slot_value=order)
        
        dispatcher.utter_message(text=str(get_query_results))

        return 


class DbQueryingMethods:
    def create_connection(db_file):
        """ 
        create a database connection to the SQLite database
        specified by the db_file
        :param db_file: database file
        :return: Connection object or None
        """
        conn = None
        try:
            conn = sqlite3.connect(db_file)
        except sqlite3.Error as e:
            print(e)

        return conn

    def select_by_slot(conn, slot_value):
        """
        Query all rows in the Orders table
        :param conn: the Connection object
        :return:
        """
        cur = conn.cursor()
        cur.execute(f'''SELECT EstimatedDeliveryDate from Orders
                    WHERE OrderID="{slot_value}"''')

        # return an array
        deliveryDate = cur.fetchall()

        if len(list(deliveryDate)) < 1:
            return "There is no such order number."
        else:
            for row in deliveryDate:
                return f"Looks like your order will be delivered by {(row[0])}."