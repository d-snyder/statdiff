import nose
import sys

sys.path.append("..")
import statdiff

argline = 'statdiff.py host:/var/opt/something/ host2:/var/opt/something/else'
statlines1 = ["-rw-r--r-- drsnyder agroup 6 1268680848 1268680849 {this is a test}.jpg .hey", "-rw-r--r-x joe joegroup 42 1268681848 1268681849 file2.jpg"]
statlines2 = [ "-rw-r--rwx fred differentgroup 37 1268680998 1268680999 {this is a test}.jpg .hey", "-rw-r--r-x fred differentgroup 37 1268680998 1268680999 file3.jpg"]

def test_args():
    subject = statdiff.StatDiff(argline.split(' '))
    print subject.subject_left
    assert 'host:/var/opt/something/' == subject.subject_left
    print subject.subject_right
    assert 'host2:/var/opt/something/else' == subject.subject_right

def test_noargs():
    exc = False
    try:
        subject = statdiff.StatDiff([])
    except Exception, e:
        assert 'You must provide at least two subjects to compare' == str(e)
        exc = True
    assert(exc)

def test_onearg():
    exc = False
    try:
        subject = statdiff.StatDiff(['this is an arg'])
    except Exception, e:
        assert 'You must provide at least two subjects to compare' == str(e)
        exc = True
    assert(exc)

def test_parselines():
    subject = statdiff.StatDiff(['fake','fake','fake'])
    stats = subject._parse_statlines(statlines1)

    stat = stats['{this is a test}.jpg .hey']

    assert stat['rights'] == '-rw-r--r--'
    assert stat['owner'] == 'drsnyder'
    assert stat['group'] == 'agroup'
    assert stat['size'] == '6'
    assert stat['atime'] == '1268680848'
    assert stat['mtime'] == '1268680849'
    assert stat['filename'] == '{this is a test}.jpg .hey'

    stat = stats['file2.jpg']

    assert stat['rights'] == '-rw-r--r-x'
    assert stat['owner'] == 'joe'
    assert stat['group'] == 'joegroup'
    assert stat['size'] == '42'
    assert stat['atime'] == '1268681848'
    assert stat['mtime'] == '1268681849'
    assert stat['filename'] == 'file2.jpg'

def test_gen_diff():
    subject = statdiff.StatDiff(['fake','fake','fake'])
    lstats = subject._parse_statlines(statlines1)
    rstats = subject._parse_statlines(statlines2)

    (diff,lextra,rextra) = subject._gen_diff(lstats,rstats)
    assert len(diff['{this is a test}.jpg .hey']) == 6
    assert diff['{this is a test}.jpg .hey']['rights'] == ['-rw-r--r--','-rw-r--rwx']
    assert diff['{this is a test}.jpg .hey']['group'] == ['agroup','differentgroup']
    assert diff['{this is a test}.jpg .hey']['owner'] == ['drsnyder','fred']
    assert diff['{this is a test}.jpg .hey']['size'] == ['6','37']
    assert diff['{this is a test}.jpg .hey']['atime'] == ['1268680848','1268680998']
    assert diff['{this is a test}.jpg .hey']['mtime'] == ['1268680849','1268680999']
    assert 'filename' not in diff['{this is a test}.jpg .hey']
    assert 'file2.jpg' in lextra
    assert 'file3.jpg' in rextra
    assert len(lextra) == 1
    assert len(rextra) == 1

def test_gen_diff_specific_keys():
    subject = statdiff.StatDiff(['fake','fake','fake'])
    lstats = subject._parse_statlines(statlines1)
    rstats = subject._parse_statlines(statlines2)

    (diff,lextra,rextra) = subject._gen_diff(lstats,rstats,['group'])
    assert len(diff['{this is a test}.jpg .hey']) == 1
    assert diff['{this is a test}.jpg .hey']['group'] == ['agroup','differentgroup']
