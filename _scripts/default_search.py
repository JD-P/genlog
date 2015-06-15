def main(searchterm, column_data):
    """Search through a data column for a given search term which is interpreted 
    as a regex."""
    try:
        pattern = re.compile(searchterm)
    except:
        return 'regex_compile_error'
    search_results = []
    for index in range(0, len(column_data)):
        item = column_data[index]
        if pattern.search(item):
                search_results.append((index, item))
    return search_results
