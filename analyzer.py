#coding=utf8
import argparse
import string
import re
import copy

example_package='''
02 
00 27 
1A 02 2F 35 02 01 00 16 25 3C 9D 9D 7C 2F BB FA 25 3C 9D 9D 7C 2F BB FA FF 00 00 
03 CC
'''


"""
Methods to translate to and from binary coded decimal
"""


def bcd_to_int(x):
    """
    This translates binary coded decimal into an integer
    TODO - more efficient algorithm
    >>> bcd_to_int(4)
    4
    >>> bcd_to_int(159)
    345
    """

    if x < 0:
        raise ValueError("Cannot be a negative integer")

    binstring = ''
    while True:
        q, r = divmod(x, 10)
        nibble = bin(r).replace('0b', "")
        while len(nibble) < 4:
            nibble = '0' + nibble
        binstring = nibble + binstring
        if q == 0:
            break
        else:
            x = q

    return int(binstring, 2)


def int_to_bcd(x):
    """
    This translates an integer into
    binary coded decimal
    >>> int_to_bcd(4)
    4
    >>> int_to_bcd(34)
    22
    """

    if x < 0:
        raise ValueError("Cannot be a negative integer")

    bcdstring = ''
    while x > 0:
        nibble = x % 16
        bcdstring = str(nibble) + bcdstring
        x >>= 4
    return int(bcdstring)

class Output:
    def __init__(self):
        self.stream = None
        return

    def push(self, streamIn):
        #todo later
        self.stream = streamIn
        return

    def flush(self):
        # todo later
        print self.stream
        return

class FormatPatten:
    offsets=0
    def __init__(self, factor, size):
        #print 'factor ' + factor+ ' size ' + size
        self._dict={}

        if factor == 'VAR':
            self._pasing_var_field(factor, size)
        else:
            self._parsing_fixed_field(factor, size)

        self.offsets = self.offsets+1
        print 'offset ' + str(self.offsets)
        #print '_dict' + str(self._dict)

    def _parsing_fixed_field(self, factor, size):
        self._dict['name']  = factor
        p=re.compile(r'\D+')
        _size = re.sub(p,'',size)
        self._dict['size'] = string.atoi(_size) * FormatPatten.BYTE_SIZE()

        p=re.compile(r'\d+')
        self._dict['indicator'] = re.sub(p,'',size)

    def _pasing_var_field(self, factor, size):
        self._dict['name']      = factor
        self._dict['indicator'] = size
        self._dict['size']      = -1
    
    @property
    def data(self):
        return self._dict

    @property
    def size(self):
        return self._dict['size']

    @size.setter
    def set_size(self, _size):
        self._dict['size'] = _size 

    @property
    def name(self):
        return self._dict['name']

    @property
    def indicator(self):
        return self._dict['indicator']

    @property
    def data(self):
        return self._dict['data']

    @data.setter
    def set_data(self, _data):
        self._dict['data'] = _data

    @staticmethod
    def genPattern(factor, size):
        return FormatPatten(factor, size)

    @staticmethod
    def BYTE_SIZE():
        return 2


class PatternReader(object):
    '''
        for handle the mpos data format
    '''
    def __init__(self, pattern):
        self._pattern = pattern

    def __read_as_BCD(self, data):
        return int_to_bcd(int(data, base=16))

    def __read_as_HEX(self, data):
        return int(data, base=16)

    def read(self):
        if self._pattern.indicator == 'HEX':
            return self.__read_as_HEX(self._pattern.data)
        elif self._pattern.indicator == 'N':
            return self.__read_as_BCD(self._pattern.data)
        else: #as a string
            return self._pattern.data

class PackageFormatter:
    def __init__(self, patternStringIn):
        self._patterns = []
        self._patterns = self.__parsing_pattern__(patternStringIn)
    
    @classmethod
    def __parsing_pattern__(_clss, patternStringIn):
        def __spit(stringIn):
            return [ln.strip() for ln in stringIn.split('|')]

        def __dict_out(stringListIn):
            _dict = {}
            if len(stringListIn) != 2:
                _dict['end']=[]
                return _dict

            p=re.compile('\s+')
            _key  = re.sub(p,'', stringListIn[0])
            _list = __spit(stringListIn[1])
            _dict[_key] = _list
            return _dict

        def __append_to(factors, sizes):
            return FormatPatten.genPattern(factors, sizes)

        _patterns = map(__dict_out, [line.split(':') for line in patternStringIn.split(';')])
        return map(__append_to, _patterns[0]['factor'], _patterns[1]['size'])

    @property
    def patterns(self):
        #print 'self._patterns' + repr(self._patterns)
        return self._patterns

    def getData(self, factor, streamIn):
        return ('','')

    def getFactors(self):
        return self.patterns.keys
    

class FormatterParserHelper(object):
    
    def __init__(self, streamIn):
        self._offset = 0
        self._stream  = streamIn
    
    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def stream(self):
        return self._stream


    def parsing(pattern):
        self.offset = self.offset+pattern.size        
        return


class RecievedPackageFormatterParserHelper(FormatterParserHelper):
    def __init__(self, streamIn):
        FormatterParserHelper.__init__(self, streamIn)
        self.__instruction = None
        self.__totallength_pattern = None

    def __parsing_var__(self, pattern, streamIn):
        _total_len    = PatternReader(self.__totallength_pattern).read() * FormatPatten.BYTE_SIZE()
        _instruction = self.__instruction.data
        pattern.size = _total_len - self.offset + FormatPatten.BYTE_SIZE() * 2 #skip 2 fields
        pattern.data = streamIn[self.offset:(self.offset+pattern.size)]
       
        self.offset = self.offset + pattern.size
        return

    def __parsing_fixed__(self,pattern, streamIn):
        pattern.data = self.stream[self.offset:(self.offset+pattern.size)]
        self.offset  = self.offset + pattern.size
        return

    def parsing(self,   pattern):
        if pattern.name=='VAR':
            self.__parsing_var__(pattern, self.stream)
        else:
            self.__parsing_fixed__(pattern, self.stream)
        
        if pattern.name == 'TOTAL_LENTH':
            self.__totallength_pattern = pattern
        elif pattern.name == 'INSTRUCTIONS':
            self.__instruction = pattern
        else:
            pass

        return pattern
        
    

class FormatterFactory(object):
    RecievedPackageFileDefinition = \
    '''
    factor  :   STX      |  TOTAL_LENTH|   INSTRUCTIONS |   INDICATOR  |    SEQUENCE   |    VAR     |   ETX   |  LRC;
    size    :   HEX1     |  N2         |   HEX2         |   HEX1       |    HEX1       |    ...     |   HEX1  |  HEX1;
    comment :   起始符    |  数据长度    |   指令号        |  指示位      |    序列号      |   可变数据域|   结束符 |  校验值;      
    '''

    ResponsePackageFileDefinition = ''

    @staticmethod
    def __parsing_as_recievedPackage(formatter, streamIn):
        helper = RecievedPackageFormatterParserHelper(streamIn)
        formatter.patterns = [helper.parsing(pattern) for pattern in formatter.patterns]
        return formatter

    @staticmethod
    def getFormatter(instrucment, streamIn):
        if instrucment == 'RecievedPackage':
            return FormatterFactory.__parsing_as_recievedPackage(PackageFormatter(FormatterFactory.RecievedPackageFileDefinition), streamIn)
        elif instrucment == 'ResponsedPackage':
            return PackageFormatter(FormatterFactory.ResponsePackageFileDefinition)
        else:
            return None

class Field:
    def __init__(self, formatPattern, dataIn):
        self.dataReader = FieldReader(indicatorIn, dataIn)
        return

    def getDATA(self):
        return self.dataReader.readAsString()

    @staticmethod
    def genField(name, indicatorIn, dataIn):
        return Field(indicatorIn, dataIn)

    @staticmethod
    def _parsing_var(pattern, streamIn):
        # formatter = FormatterFactory.getFormatter(instrucment).parsing(streamIn)
        # for f in formatter.getFactors():
        #     indicator, data  = formatter.getData(f)
        #     fields += Field.genField(indicator, data)
        return

    @staticmethod
    def __parsing_fixed_field(pattern, offset, streamIn):
        
        return

    @staticmethod
    def __parsing_var_field(pattern, offset, streamIn):
        
        return

    @staticmethod
    def parsing(direction, streamIn):
        fields = []
        offset = 0
        for pattern in FormatterFactory.getFormatter('RecievedPackage').patterns:
            if pattern.indicator == '...':
                field += Field.__parsing_var_field(pattern,   offset, streamIn)
            else:
                field += Field.__parsing_fixed_field(pattern, offset, streamIn)
            
            offset += pattern.size
            
        return []
        



class mposPackageAnalyzer:
    '''
        to analyzing the instrucment format for MPOS
    '''
    def __init__(self, packages=[]):
        self.packages = packages
        return

    def getDataFields(self, direction,packageStreamIn = None):
        return Field.parsing(direction, packageStreamIn)

    def commentFieldAsReadableString(self, field):
        
        return []

    def parsingAPackage(self, direction='Recieved',packageStreamIn=None):
        comments = []
        fields = self.getDataFields(direction,packageStreamIn)

        for field in fields:
            comments.append(self.commentFieldAsReadableString(field))
        
        return comments

    def pasing(self, output):
        for package in self.packages:
            output.push(self.getDataFields(package)).flush()
        return


# class args_parser:
#     def __init__(args):
        
#         return

# #todo later
#     def pase():
        
#         return


def test_package_formatter_parsing():
    p = re.compile(r'\W+')
    print 'example_package.strip() ' + re.sub(p, '', example_package)

    for _p in FormatterFactory.getFormatter('RecievedPackage',re.sub(p, '', example_package)).patterns:
        print 'patterns pointer ' + repr(_p)
        print 'data ' + repr(_p.data)


    #print 'patten'+ str([p.data for p in FormatterFactory.getFormatter('RecievedPackage').patterns])
    return

def test_bcd_int():
    print 'bcd %.4x' %  int_to_bcd(int('0027', base=16))
    print 'bcd2 0x%.4x ' % int('1A02 ', base=16)

if __name__ == '__main__':
    # packages = []
    # packages += example_package
    
    # console_out = Output()
    # paser = mposPackageAnalyzer(packages)
    # paser.pasing(console_out)
    test_package_formatter_parsing()
    test_bcd_int()
    pass
    




