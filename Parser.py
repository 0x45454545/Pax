from . Show import show_item

from dataclasses import dataclass as struct
from collections import deque

Epsilon    = None
Empty      = { Epsilon }
EndOfInput = "<$>"

@struct
class Grammar:

    symbol_to_id: dict[str, int]
    id_to_symbol: list[str]

    non_terminal_end: int
    symbol_count: int
    end_of_input_id: int

    production_to_id: dict[tuple[int, ...], int]
    id_to_production: list[tuple[int, ...]]

    symbol_id_to_production_ids: list[set[int]]

def construct_grammar(representation):

    symbol_to_id = { }
    id_to_symbol = [ ]

    # Pass N1 : NT
    for ID, rule in enumerate(representation.keys()):

        symbol_to_id [rule] = ID

        id_to_symbol.append( rule )

    non_terminal_end = ID

    # Pass N2 : T
    for rule, productions in representation.items():

        for production in productions:

            for symbol in production:

                if symbol not in symbol_to_id:

                    symbol_to_id [symbol] = (ID := ID + 1)

                    id_to_symbol.append( symbol )

    symbol_to_id [EndOfInput] = (ID := ID + 1)
    id_to_symbol.append( EndOfInput )

    symbol_count    = id_to_symbol.__len__()
    end_of_input_id = symbol_count - 1

    production_to_id = { }
    id_to_production = [ ]

    symbol_id_to_production_ids = [ ]

    ID = -1

    # Pass N3 : PS
    for symbol_id, (rule, productions) in enumerate(representation.items()):

        symbol_id_to_production_ids.append( set() )

        for production in productions:

            len = production.__len__()

            rhs = (symbol_to_id [symbol] for symbol in production)

            encoded = (symbol_id, len, *rhs)

            production_to_id [encoded] = (ID := ID + 1)

            id_to_production.append( encoded )

            symbol_id_to_production_ids [symbol_id].add( ID )

    return Grammar (

        symbol_to_id,
        id_to_symbol,

        non_terminal_end,
        symbol_count,
        end_of_input_id,

        production_to_id,
        id_to_production,

        symbol_id_to_production_ids

    )

def is_terminal    (grammar, symbol_id): return symbol_id >  grammar.non_terminal_end
def is_non_terminal(grammar, symbol_id): return symbol_id <= grammar.non_terminal_end

def construct_first(grammar):

    FIRST = [ set() for _ in range(grammar.symbol_count) ]

    non_terminals = range(grammar.non_terminal_end + 1)
    terminals     = range(grammar.non_terminal_end + 1, grammar.symbol_count)

    for symbol_id in terminals:

        FIRST [symbol_id].add( symbol_id )

    symbol_id_to_production_ids = grammar.symbol_id_to_production_ids
    id_to_production            = grammar.id_to_production

    new = True

    while new:

        new = False

        for symbol_id in non_terminals:

            current_first_set = FIRST [symbol_id]

            for production_id in symbol_id_to_production_ids [symbol_id]:

                lhs, len, *rhs = id_to_production [production_id]

                if len == 0:

                    if Epsilon not in current_first_set:

                        current_first_set.add( Epsilon )

                        new = True

                for inner_symbol_id in rhs:

                    inner_first_set = FIRST [inner_symbol_id]

                    pure = inner_first_set - Empty

                    if not pure.issubset(current_first_set):

                        current_first_set |= pure

                        new = True

                    if Epsilon not in inner_first_set: break

                else:

                    if Epsilon not in current_first_set:

                        current_first_set.add( Epsilon )

                        new = True

    return FIRST

def first_of_sequence(FIRST, pseudo_production):

    union = set()

    for symbol_id in pseudo_production:

        first_set = FIRST [symbol_id]

        union |= first_set - Empty

        if Epsilon not in first_set: break

    else:

        union.add( Epsilon )

    return union

def closure(grammar, FIRST, items):

    symbol_id_to_production_ids = grammar.symbol_id_to_production_ids
    id_to_production            = grammar.id_to_production

    items =   set(items)
    queue = deque(items)

    while queue:

        production_id, position, look_ahead_id = queue.popleft()

        lhs, len, *rhs = id_to_production [production_id]

        symbol_ahead_id = rhs [position] if position < len else None

        if symbol_ahead_id is None or is_terminal(grammar, symbol_ahead_id): continue

        suffix = ( * rhs [ position + 1 : ], look_ahead_id )

        look_ahead_ids = first_of_sequence(FIRST, suffix)

        production_ids = symbol_id_to_production_ids [symbol_ahead_id]

        for inner_production_id in production_ids:

            for inner_look_ahead_id in look_ahead_ids:

                item = (inner_production_id, 0, inner_look_ahead_id)

                if item in items: continue

                items   .add( item )
                queue.append( item )

    return frozenset(items)

def goto(grammar, FIRST, symbol_id, items):

    id_to_production = grammar.id_to_production

    ahead = set()

    for production_id, position, look_ahead_id in items:

        lhs, len, *rhs = id_to_production [production_id]

        if position < len and rhs [position] == symbol_id:

            ahead.add( (production_id, position + 1, look_ahead_id) )

    return closure(grammar, FIRST, ahead)

@struct
class LR1Collection:

    state_to_id: dict[frozenset[tuple[int, ...]], int]
    id_to_state: list[frozenset[tuple[int, ...]]]

    transitions: dict[tuple[int, int], int]

def construct_lr1_collection(grammar, FIRST, I0):

    ID = 0

    state_to_id = { I0 : ID }
    id_to_state = [ I0 ]
    transitions = { }

    queue = deque([ I0 ])

    while queue:

        current_state = queue.popleft()

        ids_ahead = set()

        for production_id, position, _look_ahead_id in current_state:

            lhs, len, *rhs = grammar.id_to_production [production_id]

            if position < len:

                ids_ahead.add( rhs[position] )

        for symbol_id in ids_ahead:

            if (new_state := goto(grammar, FIRST, symbol_id, current_state)):

                if new_state not in state_to_id:

                    state_to_id [ new_state ] = (ID := ID + 1)

                    id_to_state.append( new_state )

                    queue      .append( new_state )

                transitions [ (state_to_id [current_state], symbol_id) ] = state_to_id [new_state]

    return LR1Collection (

        state_to_id,
        id_to_state,

        transitions

    )

Shift  = 0
Reduce = 1
Accept = 2
Error  = 3

def report_conflict(grammar, position, action, when, given):

    state_id, ahead_id = when

    symbol_ahead = grammar.id_to_symbol [ahead_id]

    given_type, given_state_id_or_production_id = given

    if given_type == Shift:

        given_type_str = "Shift"

        given_report = f"Shift '{symbol_ahead}', I{given_state_id_or_production_id}"

    if given_type == Reduce:

        given_type_str = "Reduce"

        given_report = f"Reduce by {show_item(grammar, given_state_id_or_production_id, position, ahead_id)}"

    action_type, action_state_id_or_production_id = action

    if action_type == Shift:

        action_type_str = "Shift"

        action_report = f"Shift '{symbol_ahead}', I{action_state_id_or_production_id}"

    if action_type == Reduce:

        action_type_str = "Reduce"

        action_report = f"Reduce by {show_item(grammar, action_state_id_or_production_id, position, ahead_id)}"

    print(
        f"{action_type_str}/{given_type_str} conflict:\n"
        f"    When I{state_id} on '{symbol_ahead}':\n"
        f"        {action_report};\n"
        f"    Or\n"
        f"        {given_report};\n"
    )

def construct_action(grammar, lr1_collection):

    id_to_production = grammar.id_to_production

    id_to_state = lr1_collection.id_to_state
    transitions = lr1_collection.transitions

    ACTION = { }
    ACTION_KIND = 0

    for state_id, state in enumerate(id_to_state):

        for production_id, position, look_ahead_id in state:

            lhs, len, *rhs = id_to_production [production_id]

            if position < len:

                symbol_ahead_id = rhs [position]

                if is_terminal(grammar, symbol_ahead_id):

                    when = (state_id, symbol_ahead_id)

                    next_state = transitions [when]

                    shift = (Shift, next_state)

                    if when in ACTION:

                        given = ACTION [when]

                        if given [ACTION_KIND] == Reduce:

                            report_conflict(grammar, position, shift, when, given)

                            return False

                    ACTION [when] = shift

                continue

            # pos >= len -> @ end of production

            when = (state_id, look_ahead_id)

            if production_id == 0 and look_ahead_id == grammar.end_of_input_id:

                ACTION [when] = (Accept, )

                continue

            reduce = (Reduce, production_id)

            if when in ACTION:

                given = ACTION [when]

                report_conflict(grammar, position, reduce, when, given)

                return False

            ACTION [when] = reduce

    return ACTION

def construct_goto(grammar, lr1_collection):

    return {

        (state_id, symbol_id) : next_state_id

        for (state_id, symbol_id), next_state_id in lr1_collection.transitions.items()

        if is_non_terminal(grammar, symbol_id)

    }
