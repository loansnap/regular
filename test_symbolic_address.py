from .format import clean, format
from .match import match
from .symbol import S, TransSymbol as Trans
from .symbolic_address import SymbolicAddress

import json, os, unittest
module_dir = os.path.dirname(__file__)


class TestSymbolicAddress(unittest.TestCase):
    def test_dot(self):
        w = SymbolicAddress('w')
        template = {'a':{'b':w.x, 'c':w.y.v}, 'd':w.y.u}

        expansion = SymbolicAddress.get_expansion(template)
        self.assertEqual(expansion, {'w': {'y': {'v': S('w.y.v'), 'u': S('w.y.u')}, 'x': S('w.x')}})

    def test_indexing(self):
        loan = SymbolicAddress('loan')
        template = {'borrowers': [{'name': loan.applications[{'appIndex':0}].borrower.name},
                                  {'name': loan.applications[{'appIndex':0}].coborrower.name}]}

        expansion = SymbolicAddress.get_expansion(template)
        self.assertEqual(expansion, {'loan': {'applications': [
            {'appIndex': 0,
             'coborrower': {'name': S("loan.applications[{'appIndex': 0}].coborrower.name")},
             'borrower': {'name': S("loan.applications[{'appIndex': 0}].borrower.name")}}
        ]}})

    def test_reverse_format(self):
        data = [{'name': 'john', 'addresses': [{'state': 'CA'}, {'state': 'CT'}]},
                {'name': 'allan', 'addresses': [{'state': 'CA'}, {'state': 'WA'}]}]
        record = SymbolicAddress('record')
        template = [{'name': record.name, 'addresses': [{'state': record.state}]}]

        m = match(template, data)
        result = SymbolicAddress.reverse_format(template, m)
        # Note that only one result is returned
        self.assertEqual(result, {'record': {'name': 'john', 'state': 'CA'}})

    def test_tranformation_function(self):
        data = {"propertyEstimatedValueAmount": 400000.0}
        application = SymbolicAddress('application')
        template = {'propertyEstimatedValueAmount': Trans(application.hypothetical_mortgage.property.estimated_value_amount, int)}

        m = match(template, data)
        result = SymbolicAddress.reverse_format(template, m)
        self.assertEqual(result, {'application':{'hypothetical_mortgage': {'property': {'estimated_value_amount': 400000}}}})

    def test_transformation_map(self):
        data = {'name':'John'}
        application = SymbolicAddress('application')
        template = {'name': Trans(application.hypothetical_mortgage.name, {'john':'John'})}

        m = match(template, data)
        result = SymbolicAddress.reverse_format(template, m)
        self.assertEqual(result, {'application': {'hypothetical_mortgage': {'name': 'john'}}})
