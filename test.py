import responses
from .match import match
from .format import format
from .symbol import S, Nullable, TransSymbol as Trans

import random, unittest


class TestFull(unittest.TestCase):
    # Test 1: Single match, no lists
    @responses.activate
    def test_single_match(self):
        data = {'name': 'john'}
        template = {'name': S('name')}

        m = match(template, data)
        result = format(template, m)
        self.assertEqual(result, data)

    # Test 2: Two matches
    @responses.activate
    def test_two_matches(self):
        data = [{'name':'john'}, {'name':'abe'}]
        template = [{'name': S('name')}]

        m = match(template, data)
        result = format(template, m)
        self.assertEqual(result, data)

    # Test 3: Transposition
    @responses.activate
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
    @responses.activate
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
    @responses.activate
    def test_nullable(self):
        data = {}
        template = {'person': Nullable([{'name':S('name')}])}

        m = match(template, data).get_single()  # Should not raise an exception

    # Test 6: Nullable conserved by format when symbols remain
    @responses.activate
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
    @responses.activate
    def test_transformation(self):
        data = {'state':'California'}
        template = {'state': Trans(S('state'), {'CA': 'California'})}

        m = match(template, data)
        self.assertEqual(m.get_single()['state'], 'CA')

        result = format(template, m)
        self.assertEqual(result, data)

    # Test 7.5: Transformation closed-loop test with function transformation
    def test_transformation_2(self):
        data = {'yrs': 12.5}
        parse_template = {'yrs': S('yrs')}
        format_template = {'residency': Trans(S('yrs'), int)}

        m = match(parse_template, data)
        result = format(format_template, m)
        self.assertEqual(result, {'residency': 12})

    # Test 8: Join on a repeated symbol
    def test_join(self):
        data = {'names': [{'ssn': 123456789, 'name': 'mario'}, {'ssn': 987654321, 'name': 'luigi'}],
                'hats': [{'ssn': 123456789, 'hat_color': 'red'}, {'ssn': 987654321, 'hat_color': 'green'}]}
        match_template = {'names': [{'ssn': S('ssn'), 'name':S('name')}],
                          'hats': [{'ssn': S('ssn'), 'hat_color': S('color')}]}
        format_template = [{'name': S('name'), 'ssn': S('ssn'), 'color': S('color')}]
        # NOTE: one major drawback of the current code is that format() must USE a symbol in order to join on it.
        # E.g., this example would do a full cartesian product rather than a join if S('ssn') were omitted from format_template.
        expected = [{'name': 'mario', 'ssn': 123456789, 'color': 'red'},
                    {'name': 'luigi', 'ssn': 987654321, 'color': 'green'}]

        m = match(match_template, data)
        result = format(format_template, m)
        self.assertEqual(result, expected)

    # Tests 9 & 10: More general Transformation usage
    def test_multi_transformation_forward(self):
        data = [{'name': 'john', 'addresses': [{'state': 'CA'}, {'state': 'CT'}]},
                {'name': 'allan', 'addresses': [{'state': 'CA'}, {'state': 'WA'}]}]
        match_template = [{'name': S('name'), 'addresses': [{'state': S('state')}]}]
        starts_j = lambda name: name[0] == 'j'
        format_template = [{'address': {'state': S('state')}, 'names': Trans([S('name')], lambda names: list(filter(starts_j, names)))}]
        expected = [{'address': {'state': 'CA'}, 'names': ['john']},
                    {'address': {'state': 'CT'}, 'names': ['john']},
                    {'address': {'state': 'WA'}, 'names': []}]

        m = match(match_template, data)
        result = format(format_template, m)
        self.assertEqual(result, expected)

    def test_multi_transformation_reverse(self):
        data = {'names': [{'ssn': 'red', 'name': 'mario'}, {'ssn': 'green', 'name': 'luigi'}],
                'hats': [{'ssn': 123456789, 'hat_color': 'red'}, {'ssn': 987654321, 'hat_color': 'green'}]}
        switcheroo = lambda hat_entry: {'ssn': hat_entry['hat_color'], 'hat_color': hat_entry['ssn']}
        match_template = {'names': [{'ssn': S('ssn'), 'name':S('name')}],
                          'hats': [Trans({'ssn': S('ssn'), 'hat_color': S('color')}, reverse=switcheroo)]}
        format_template = [{'name': S('name'), 'ssn': S('ssn'), 'color': S('color')}]
        expected = [{'name': 'mario', 'ssn': 'red', 'color': 123456789},
                    {'name': 'luigi', 'ssn': 'green', 'color': 987654321}]

        m = match(match_template, data)
        result = format(format_template, m)
        self.assertEqual(result, expected)

    # TransSymbol invertibility: things were failing if forward(reverse(x)) != x. Fixed now.
    # Found this one out the hard way - h/t Marc
    def test_trans_list_bug(self):
        match_template = {
            "create_date": Trans(S('created_at'), reverse=lambda x: x + '!'),
            "actions": [{
                "date": S('velocify_action_date'),
            }]
        }

        template = {
            "created": S('created_at'),
            "velocify": {
                "actions": [{
                    "date": S('velocify_action_date'),
                }]
            }
        }

        data = {'create_date': '2017-12-12 07:39:06', 'actions': [{'date': '2017-12-11 11:40:56'}, {'date': '2017-12-18 11:49:56'}]}
        expected = {'created': '2017-12-12 07:39:06!', 'velocify': {'actions': [{'date': '2017-12-11 11:40:56'}, {'date': '2017-12-18 11:49:56'}]}}

        m = match(match_template, data)
        result = format(template, m)
        self.assertEqual(result, expected)

    # Test 12: Make sure TransSymbol doesn't swallow errors
    def test_trans_error(self):
        data = {'yrs': 'foo'}
        parse_template = {'yrs': S('yrs')}
        format_template = {'residency': Trans(S('yrs'), int)}

        m = match(parse_template, data)
        err = None
        try:
            result = format(format_template, m)
        except ValueError as e:
            err = e
        self.assertIsNotNone(err)

# This test recreates an issue seen here: https://www.pivotaltracker.com/story/show/166254857
# where we are trying to match several specific dicts based on a key and that key is repeated multiple times
# only hits when the number of duplicates is sufficiently high
class TestPerf(unittest.TestCase):
    def generate_template_and_values(self, number_of_titles, number_or_repeats_for_each_title):
        # create an list of elements where the titles are the string version of an integer (for easy generation)
        # also creates a template that looks for these titles
        values = []
        template = []
        for n in list(range(number_of_titles)):
            template.append(Nullable({ 'title': S(str(n))}))
            # add number_or_repeats_for_each_title of each as the "title" of the dict
            for i in list(range(number_or_repeats_for_each_title)):
                values.append({ 'title': str(n)})
        return (template, values)

    def test_few_iterations(self):
        # this one will work with only a few iterations and repeats
        template, values = self.generate_template_and_values(3, 3)
        result = match(template, values).get_single()
        self.assertTrue(result)

    def test_many_iterations(self):
        # this one will work with only a few iterations and repeats
        template, values = self.generate_template_and_values(20, 5)
        result = match(template, values).get_single()
        # this code will never run b/c it stalls
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
