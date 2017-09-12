At its core, Regular provides regexes (a.k.a. Regular language capabilities) for non-strings.

# Simple Examples
Here’s a few examples of what this looks like. First, a plain old python regex example for comparison:
```python
>>> m = re.match(r"(?P<first_name>\w+) (?P<last_name>\w+)", "Malcolm Reynolds")
>>> m.group('first_name')
'Malcolm'
>>> m.group('last_name')
'Reynolds'
```
Now, compare to a simple Regular example:
```python
>>> list(match({"firstName": S("first"), "lastName": S("last")}, {"firstName": "Malcolm", "lastName": "Reynolds"}))
[{S("first"): "Malcolm", S("last"): "Reynolds"}]
```
… exactly what you’d expect, but not very impressive. We can make it a little more interesting with deeper structures:
```python
>>> list(match({"actor": {"name": {"firstName": S("first"), "lastName": S("last")}}}, {"actor":{"otherInfo":..., "name": {"firstName": "Malcolm", "lastName": "Reynolds", "middleInitial": "", ...}}}))
[{S("first"): "Malcolm", S("last"): "Reynolds"}]
```
Now it’s starting to look like a lightweight parser. And that’s exactly what Regular is - a lightweight parser, just like regexes. Rather than parsing strings, it parses json-style data structures.

Why would you want to parse json-style structures? The main reason is for translating between schemas. For instance, building on the previous example:
```python
>>> m = match({"actor": {"name": {"firstName": S("first"), "lastName": S("last")}}}, {"actor":{"otherInfo":..., "name": {"firstName": "Malcolm", "lastName": "Reynolds", "middleInitial": "", ...}}})
>>> list(m)
[{S("first"): "Malcolm", S("last"): "Reynolds"}]
>>> format(m, {"client": {"occupation": "actor", "first_name": S("first"), "last_name": S("last")}})
{"client": {"occupation": "actor", "first_name": "Malcolm", "last_name": "Reynolds"}}
```

That’s handy, but the value add is underwhelming. We could do the same thing with e.g.
```python
{"client": {"occupation": "actor", "first_name": data.actor.name.firstName, "last_name": data.actor.name.lastName}}
```
So what's the value add from using Regular? Well, the Regular approach:
- saves writing lots of guards for missing fields
- gives both a forward and reverse map in one fell swoop
- gives a data structure which can be queried for programmatic analysis of data flows
That last point is especially important. By representing mappings as a data structure, we open the door to developer tools for tracing where a given field comes from and goes to. If e.g. an LO points out that we're incorrectly populating a field in encompass, then we can easily (and automatically) trace that field id back through Regular maps to its ultimate source.

Another useful value add comes when our data contains lists. Suppose that the target schema has a field "contractor_phone", which we wish to populate from the source schema. The source schema has a list of contacts, one of which has "type":"contractor". Rather than writing a for-loop, Regular lets us write code like this:
```python
>>> m = match({contacts:[{"type":"contractor", "phone":S("contractor_phone")}]}, {contacts:[{"type":"banker", ...},{"type":"contractor", "phone":"555-555-5555"}]})
>>> m
{"contractor_phone":"555-555-5555"}
```
No for-loops were harmed in the making of this code.

(That’s everything we need for the old encompass <-> new encompass mapping. The next section addresses the more powerful features we need for pretty much any other mapping.)


# Not-So-Simple Examples
Now for a more complicated example: structure mapping. Suppose that both the source and target schema contain corresponding lists, and we wish to map between them.
```python
>>> m = match({contacts:[{"phone":S("phone")}]}, {contacts:[{"type":"banker", "phone":"444-444-4444"},{"type":"contractor", "phone":"555-555-5555"}]})
>>> list(m)
[{"phone":"444-444-4444"}, {"phone":"555-555-5555"}]
```
Notice what happened here: there were multiple possible matches, so a list of the possible matches was returned. Now, we pass that list into format():
```python
>>> format(m, {"users": [{"source":"contacts", "number":S("phone")}]})
{"users":[{"source":"contacts", "number":"444-444-4444"}, {"source":"contacts", "number":"555-555-5555"}]}
```
Each possible match produced a list element in the target schema.

In general, it’s not quite so simple as producing a list element in the target schema for each element in the source - there are nesting levels to think about. When dealing with nesting, Regular’s policy is to avoid duplicating data whenever possible. Here's an example, in which a data structure is transposed:
```python
>>> data = [{'name':'john', 'addresses':[{'state':'CA'}, {'state':'CT'}]},
            {'name': 'allan', 'addresses':[{'state':'CA'}, {'state':'WA'}]}]
>>> match_template = [{'name':S('name'), 'addresses':[{'state':S('state')}]}]
>>> format_template = [{'address':{'state':S('state')}, 'names':[S('name')]}]
>>> m = match(match_template, data)
>>> format(format_template, m)
    [{'address':{'state':'CA'}, 'names':['john', 'allan']},
     {'address':{'state':'CT'}, 'names':['john']},
     {'address':{'state':'WA'}, 'names':['allan']}]
```

Another issue is cartesian products, where two fields have multiple independent matches. For example:
```python
>>> data = {'x':[1, 2, 3],
            'y':[4, 5, 6]}
>>> template = {'x':[S('x')], 'y':[S('y')]}
>>> list(match(template, data))
    [{S('x'): 1, S('y'): 4}, {S('x'): 1, S('y'): 5}, {S('x'): 1, S('y'): 6}, {S('x'): 2, S('y'): 4},...,  {S('x'): 3, S('y'): 6}]
```
As the number of variables with multiple independent matches grows, the list of possible matches grows exponentially. The match structure represents these efficiently; be careful about serializing it. When a match object is passed directly to format(), the full list of matches is not generated (assuming the target format also represents the variables independently).

[TODO: add a section here on SymbolicAddress and other features.]


# Why?
Regular is ultimately useful because it allows us to replace functions with data structures. When a function is represented by a data structure, we can automatically do things like:
- Compute the inverse function (i.e. reverse a map)
- Compute composite functions (i.e. construct an A <-> B map from A <-> C and B <-> C)
- Visualize and programmatically query data flow (i.e. see where a field comes from without reading through code)
- Serialize and pass around functions (i.e. let frontend know where LTV breakpoints are)
All the theory-talk is because turing complete data structures are a pain in the ass. In order to get data structures which are reasonable to deal with, we need to use a weaker language. In general, weaker languages allow simpler data structures - expanding to the power of CFGs would make the structures much more complicated.


# FAQ
Q: Should Regular handle all of our schema-mapping needs?

A: Do regular expressions handle all of your parsing needs?

Q: So when should I use Regular?

A: It should handle the lion’s share of mapping between any two schemas. It won’t handle everything - there will be weird cases.

Q: What won’t it handle?

A: You’ll need to know the schema in advance, and the schema should be tree-shaped - this is a regular language library, after all. No recursive schemas, and DAG schemas will be split into trees.

Q: How can I pick out a list element by index?

A: If and when it becomes necessary, I will add a magic keyword for that: "_index".
