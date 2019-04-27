def input_wrapper(prompt, options=None, brackets_type='*'):
    """
    Wrapper for input() to enforce user chooses out of a predetermined list of options
    [brackets_type] prompt (options):>

    :param prompt: str, the string to prompt for input
    :param options: list, if used it enforces input to a selection over the elements
    :param brackets_type: str,  what goes between the newline brackets
    :return: str, what the user inputed
    """
    response = ''
    if options:
        while response.lower() not in options:
            response = input(('\r[%s]%s (%s) :>' % (brackets_type, prompt, ', '.join(options))))
    else:
        response = input(('\r[%s]%s :>' % (brackets_type, prompt)))

    return response
