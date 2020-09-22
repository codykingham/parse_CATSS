import re
from pathlib import Path
from regex_patterns import ref_string
from datetime import datetime

def patch(data_dir='source', output_dir='source/patched', silent=False):
    """Corrects known errors in the CATSS database."""

    log = ''
    log += datetime.now().__str__() + '\n'

    def report(msg):
        # give feedback
        nonlocal log # see https://stackoverflow.com/a/8178808/8351428
        log += msg + '\n'
        if not silent:
            print(msg)
    
    data = Path(data_dir)
    file2lines = {}

    for file in data.glob('*.par'):
        file2lines[file.name] = file.read_text().split('\n')

    # -- Manual Edits --

    # manual corrections loaded into tuples consisting of:
    # (file, line_number, regex condition, new line)
    # where line numbers refer to the original line numbers in the docs,
    # the regex condition is a pattern to search all in the line to confirm the 
    # change (a safeguard for erroneous changes or for when the underlying data
    # changes). All of the changes are enacted in a large loop.
    # If filename is left empty, the previous filename is used
    # NB: linenumbers are given as 0-indexed
    edits = [
        ('06.JoshB.par', 983, 'MRY KAI', 'W/)T H/GRG$Y ^ =W/)T W/H/)MRY\t KAI\\ TO\\N AMORRAI=ON '),
        ('', 1366, '\.kb # KAI', 'W/H/KHNYM =W/H/)BNYM .m .kb #\t KAI\\ OI( LI/QOI '),
        ('', 3737, '12 E', 'W/YC+YRW =;W/YC+YDW .rd <9.12>\t E)PESITI/SANTO {d} KAI\\ H(TOIMA/SANTO'), 
        ('', 9517, '<19.49> E', "--+ '' =;L/GBWLWT/YHM <19.49>\t E)N TOI=S O(RI/OIS AU)TW=N "),
        ('', 2006, '\t<6.20>\t', '-+ =;H/(YR/H <6.20>\tEI)S TH\\N PO/LIN '),
        ('', 9515, '\t<19\.49>\t', "--+ '' =;M/XLQ <19.49>\tDIAMERI/SAS "),
        ('01.Genesis.par', 9550, "--\+ ' ", "--+ '' =;W/BH <24.14>\tKAI\ E)N TOU/TW|"),
        ('', 9552, "--\+ ' ", "--\+ '' =;KY <24.14>\tO(/TI"),
        ('17.1Esdras.par', 477, 'CC35\.24', 'W/Y(BYR/HW\tKAI\\ {..^A)PE/STHSAN AU)TO\\N} [cc35.24]'),
        ('27.Sirach.par', 4843, '{\.\.}', '[..]\tA)PO\\'),
        ('11.1Sam.par', 2096, 'O\t', "--+ '' =KPWT\tOI( KARPOI\\"),
        ('', 2097, 'T\t', "--+ '' =;YD/YW\tTW=N XEIRW=N AU)TOU="),
        ('13.1Kings.par', 15936, 'EI\)S}\t', "W/YBW)\tKAI\ EI)SH=LQEN {...EI)S}"),
        ('26.Job.par', 2245, 'OU\)}\t', "W/L)\t{..^OU)}DE\\"),
        ('44.Ezekiel.par', 471, 'OU=} MDBR', "MDBR =v\t{...?AU)TOU=} LALOU=NTOS"),
    ]

    report('\napplying bulk manual edits...\n')

    file = ''
    for edit in edits:

        # unpack data
        file = edit[0] or file
        ln, re_confirm, redaction = edit[1:]
        old_line = file2lines[file][ln]

        # confirm and apply changes, give reports throughout
        if re.findall(re_confirm, old_line):
            file2lines[file][ln] = redaction
            report(f'correction for {file} line {ln}:')
            report(f'\tOLD: {old_line}')
            report(f'\tNEW: {redaction}')
        else:
            report(f'**WARNING: THE FOLLOWING EDIT WAS NOT CONFIRMED**:')
            report(f'\tOLD: {old_line}')
            report(f'\tEDIT: {(file, ln, re_confirm, redaction)}')

    # -- Other Edits --

    # there is a corruption in the lines for Exod 35:19:
    # 
    #     16283 ^ ^^^ =L/$RT {...?H/&RD} #  {+} E)N AI(=S LEITOURGH/SOUSIN
    #     16284 
    #     16285 Exod 1:10
    #     16286     #
    #     16287 
    #     16288 Exod 35:19
    #     16289 --+ E)N AU)TAI=S 
    #
    # the interposition of blank lines and the "Exod 1:10" string are not
    # supposed to be there, and they interrupt the data-lines for Exod 35:19
    # these incorrect lines will be removed; the extra Exod 35:19 heading will
    # likewise become unnecessary
    # NB that line numbers below will be 1 less due to zero-indexing of Python
    
    # first check that the edit still applies to current file
    exod = file2lines['02.Exodus.par']
    if exod[16284] == 'Exod 1:10':
        report('patching corrupt lines 16283-16289 in 02.Exodus.par...')
        fixed_lines = exod[:16283] + [exod[16285]] + exod[16288:]
        file2lines['02.Exodus.par'] = fixed_lines
        report('\tdone')
    else:
        report('**WARNING: SKIPPING EXODUS CORRUPTION REPAIR DUE TO CHANGED LINE NUMBERS; see code')

    # orphaned lines are cases where parts of a line are inexplicably broken off
    # these are handled in bulk in a loop further below; but Ps 68:31 contains a 
    # special case with 2 orphaned lines in a row
    # to prevent need for recursive algorith, we just fix it manually
    # we do it here to avoid needed to adjust indices after the correction
    # listed subsequent to this one
    pss = file2lines['20.Psalms.par']
    if pss[10848] == 'MTR':
        report('patching double-orphaned lines in lines 10849-10851 of 20.Psalms.par (Ps 68:31)')
        ps68_31_patch = [pss[10848] + pss[10849] + pss[10850]]
        file2lines['20.Psalms.par'] = pss[:10848] + ps68_31_patch + pss[10851:] 
        report('\tdone')
    else:
        report('**WARNING: SKIPPING PSALMS ORPHAN REPAIR DUE TO CHANGED LINE NUMBERS; see code')

    # An identical corruption to the one discussed above in Exodus 35:15
    # likewise in 20.Psalms.par lines 2455-2459
    if pss[2459] == 'Ps 18:40':
        report('patching corrupt lines 2457-2461 in 20.Psalms.par...')
        fixed_lines = pss[:2456] + [pss[2457]] + pss[2460:]
        file2lines['20.Psalms.par'] = fixed_lines
        report('\tdone')
    else:
        report('**WARNING: SKIPPING PSALMS ORPHAN REPAIR #2 DUE TO CHANGED LINE NUMBERS; see code')

    # -- Repair Orphaned Lines --

    # a search for lines without \t reveals that numerous lines are 
    # orphaned from their original line, for instance, see DanTh 6:17:
    # >>> 4132     L/DNY)L ,,a TO\N
    # >>> 4133     DANIHL
    # here DANIHL should be a part of the previous line
    # this problem is found in Sirach, Psalms, Daniel, Chronicles, Ezekiel, Neh,
    # etc. and is correlated with the book names. For instance, in the Psalms,
    # the Hebrew column is affected anywhere the characters "PS" appear (פס)
    # In Deuteronomy, the Greek column is affected where DEUT appears in the text
    # This was probably caused by a bad export and regex pattern that inserted a 
    # newline everywhere a book reference was found in the database, with the ill-effect
    # that text containing the first characters of the books were also cleft by the newline. 
    # Since most book abbreviations contain vowels, the Greek column is primarily affected,
    # meaning that orphaned lines need to be shifted up and appended to the Greek column.
    # The one exception to this is Psalms with the "PS" string that is anywhere a 
    # פס appears in the text. These cases need to be merged down to the BEGINNING of the 
    # subsequent line, in the Hebrew column.
    # This script will provide a detailed report in the log about which passages are affected,
    # as well as how these effects are corrected (either shift up or shift down).

    # TODO: This could be better patched by doing a simple search/replace in the text 
    # for all text beginning with book names and preceded by a newline
    # will need a regex pattern that can differentiate genuine booknames and text

    report('patching orphaned lines (see code for description)...')

    current_verse = None
    for file, lines in file2lines.items():

        filtered_lines = []

        i = 0
        while i < len(lines):

            line = lines[i]

            # track references and keep them
            if ref_string.match(line):
                current_verse = line
                filtered_lines.append(line)
            
            # apply corrections to relevant lines
            elif line and '\t' not in line:
                
                # append to log and report which lines are involved
                show = f'\n\t\t{lines[i-1]}\n\t--> {line}\n\t\t{lines[i+1]}'
                report(f'\tpatching {file} at line {i}, {current_verse}:{show}')

                # shift line down to HB col if it's in Psalms
                if current_verse.startswith('Ps'):
                    filtered_lines.append(line+lines[i+1])
                    i += 1 # shift forward 1 extra to skip already-covered line

                # otherwise shift it up to GK col
                else:
                    filtered_lines[-1] = filtered_lines[-1] + line

            # keep everything else unchanged            
            else:
                filtered_lines.append(line) 

            # advance the position 
            i += 1

        # reassign to new lines
        file2lines[file] = filtered_lines

    report('\tdone')

    # -- Bulk Normalizations -- 
    
    # changes which need to be effected systematically are loaded into tuples:
    # (regex, replace)
    # the changes are enacted with regex substitutions
    # not all of these are stricly errors (though they may be), there 
    # are numerous cases of normalizations applied to bring idiosyncratic
    # patterns in line with the majority

    normalizations = [
        ('~', '^'),
        ("(['^])=", '\g<1> ='), # accidental fusions to `=` on left side
    ]

    report('\nMaking various bulk regex normalizations...\n')

    for search, replace in normalizations:

        search = re.compile(search) # compile for efficiency

        for file, lines in file2lines.items():
        
            new_lines = []
            curr_verse = ''

            for i,line in enumerate(lines):
                
                # track passages for reporting since line numbers have already changed
                if ref_string.match(line):
                    curr_verse = line
                    new_lines.append(line)

                # apply substitutions
                if search.findall(line):
                    redaction = search.sub(replace, line)
                    new_lines.append(redaction)
                    report(f'normalization in {file} in {curr_verse}:')
                    report(f'\tOLD: {line}')
                    report(f'\tNEW: {redaction}')
                
                # else keep line the same
                else:
                    new_lines.append(line)

            file2lines[file] = new_lines

    # export the corrected files
    report(f'writing patched data to {output_dir}')
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()

    for file, lines in file2lines.items():
        text = '\n'.join(lines)
        file_path = output_dir.joinpath(file)
        file_path.write_text(text)

    # write changes to a log file
    log_path = output_dir.joinpath('log.txt')
    log_path.write_text(log)

    report('DONE with all patches!')
