from .match import match
from .format import format
from .symbol import S, Nullable, TransSymbol as Trans

import random, unittest


class TestFull(unittest.TestCase):
    # Test 1: Single match, no lists
    def test_single_match(self):
        data = {'name': 'john'}
        template = {'name': S('name')}

        m = match(template, data)
        result = format(template, m)
        self.assertEqual(result, data)
    
    # Test 2: Two matches
    def test_two_matches(self):
        data = [{'name':'john'}, {'name':'abe'}]
        template = [{'name': S('name')}]

        m = match(template, data)
        result = format(template, m)
        self.assertEqual(result, data)
    
    # Test 3: Transposition
    def test_transposition(self):
        data = [{'name':'john', 'addresses':[{'state':'CA'}, {'state':'CT'}]},
                {'name': 'allan', 'addresses':[{'state':'CA'}, {'state':'WA'}]}]
        match_template = [{'name':S('name'), 'addresses':[{'state':S('state')}]}]
        format_template = [{'address':{'state':S('state')}, 'names':[S('name')]}]
        expected = [{'address':{'state':'CA'}, 'names':['john', 'allan']},
                    {'address':{'state':'CT'}, 'names':['john']},
                    {'address':{'state':'WA'}, 'names':['allan']}]

        m = match(match_template, data)
        result = format(format_template, m)
        self.assertEqual(result, expected)
    
    # Test 4: Cartesian product stress test
    def test_cartesian_product(self):
        data = {'u':[random.random() for i in range(1000)],
                'v':[random.random() for i in range(1000)],
                'w':[random.random() for i in range(1000)],
                'x':[random.random() for i in range(1000)],
                'y':[random.random() for i in range(1000)],
                'z':[random.random() for i in range(1000)]}
        template = {'u':[S('u')], 'v':[S('v')], 'w':[S('w')], 'x':[S('x')], 'y':[S('y')], 'z':[S('z')]}

        m = match(template, data) # Should take several decades if cartesian products are handled naively
        result = format(template, m)
        self.assertEqual(result, data)

    # Test 5: Nullable
    def test_nullable(self):
        data = {}
        template = {'person': Nullable([{'name':S('name')}])}

        m = match(template, data).get_single()  # Should not raise an exception

    # Test 6: Nullable conserved by format when symbols remain
    def test_nullable_conserved(self):
        data = {'state':'CA'}
        template = {'person': Nullable([{'name':S('name')}]), 'state':S('state')}

        template = format(template, {S('state'): 'CA'})
        m = match(template, data).get_single()  # Should not raise an exception

        template = format(template, {S('name'):'john'})
        exception = None
        try:
            m = match(template, data).get_single()  # Should raise an exception
        except Exception as e:
            exception = e
        self.assertIsNotNone(exception)

    # Test 7: Transformation closed-loop test
    def test_transformation(self):
        data = {'state':'California'}
        template = {'state': Trans(S('state'), {'CA': 'California'})}

        m = match(template, data)
        self.assertEqual(m.get_single(), {S('state'): 'CA'})

        result = format(template, m)
        self.assertEqual(result, data)


if __name__ == '__main__':
    unittest.main()
