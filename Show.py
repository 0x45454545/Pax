# DEBUG FILE

def is_non_terminal(grammar, symbol_id): return symbol_id <= grammar.non_terminal_end

def show_production(grammar, production_id):

    lhs, len, *rhs = grammar.id_to_production [production_id]

    lhs_repr = grammar.id_to_symbol [lhs]

    rhs_repr = ' '.join(
        (
            grammar.id_to_symbol [symbol_id]

            if is_non_terminal(grammar, symbol_id) else

            f"'{grammar.id_to_symbol [symbol_id]}'"
        )
        for symbol_id in rhs
    )

    return f"{lhs_repr:} -> {rhs_repr:}"

def show_item(grammar, production_id, position, look_ahead_id):

    lhs, len, *rhs = grammar.id_to_production [production_id]

    lhs_repr = grammar.id_to_symbol [lhs]

    rhs_l_repr = ' '.join(
        (
            grammar.id_to_symbol [symbol_id]

            if is_non_terminal(grammar, symbol_id) else

            f"'{grammar.id_to_symbol [symbol_id]}'"
        )
        for symbol_id in rhs[0:position]
    )

    rhs_r_repr = ' '.join(
        (
            grammar.id_to_symbol [symbol_id]

            if is_non_terminal(grammar, symbol_id) else

            f"'{grammar.id_to_symbol [symbol_id]}'"
        )
        for symbol_id in rhs[position:]
    )

    dot = '!'

    rhs_repr = ""

    if rhs_l_repr:
        rhs_repr += f"{rhs_l_repr} "

    rhs_repr += dot

    if rhs_r_repr:
        rhs_repr += f" {rhs_r_repr}"

    ahead_repr = f"'{grammar.id_to_symbol [look_ahead_id]}'"

    return f"{lhs_repr:>10} -> {rhs_repr:<16} , {ahead_repr}"

class Action:
    Shift  = 0
    Reduce = 1
    Accept = 2

def show_action(grammar, action):

    match action:

        case (Action.Shift, next_state_id):

            action_repr = f"Shift I{next_state_id}"

        case (Action.Reduce, production_id):

            action_repr = f"Reduce by: {show_production(grammar, production_id)}"

        case (Action.Accept,):

            action_repr = f"Accept"

    return action_repr

def dissect(grammar, FIRST, lr1_collection, ACTION, GOTO):

    for state_id, state in enumerate(lr1_collection.id_to_state):

        print(f"--- I{state_id}: ---")

        print(f"  Items:")

        for production_id, position, look_ahead_id in state:

            production_repr = show_item(grammar, production_id, position, look_ahead_id)

            print(f"    {production_repr}")

        print(f"  Actions:")

        for symbol_id in range(grammar.symbol_count):

            when = (state_id, symbol_id)

            if when in ACTION:

                action = ACTION [when]

                action_repr = show_action(grammar, action)

                ahead_repr = f"'{grammar.id_to_symbol [symbol_id]}'"

                print(f"    {ahead_repr:>10} {action_repr}")

        print(f"  Goto:")

        for symbol_id in range(grammar.non_terminal_end + 1):

            when = (state_id, symbol_id)

            if when in GOTO:

                goto = GOTO [when]

                goto_repr = f"I{goto}"

                symbol_repr = grammar.id_to_symbol [symbol_id]

                print(f"    {symbol_repr:>10} -> {goto_repr:<3}")

        print()

    print()
