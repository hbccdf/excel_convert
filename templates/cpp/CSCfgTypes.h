#pragma once
#include <string>
#include <vector>
#include <map>
#include "FBAll_Const.h"
#include "BufferReader.hpp"
#include <network/meta/meta.hpp>
#include <fmt/format.h>

<%def name='field_type(type_name)'>\
<%
    return f'{type_name:>15s}'
%>\
</%def>\
<%def name='field_default_value(field)'>\
<%
    if field.has_default_value:
        return f'{{{field.default_value}}}'
    else:
        return ''
%>\
</%def>\
<%def name='field_desc(field)'>\
<%
    if field.desc != '':
        return f' //{field.desc}'
    else:
        return ''
%>\
</%def>\
<%def name='field_define(field)'>\
<%
    return f'{field.name}{field_default_value(field)};{field_desc(field)}'
%>\
</%def>\
namespace GameConfig
{
    using namespace std;

    //enums
    % for _, enum_type in all.enums.items():
    % if enum_type.is_enum_class:
    enum class ${enum_type.code_name}
    % else:
    enum ${enum_type.code_name}
    % endif
    {
        % for field in enum_type.fields:
        ${field.code_name} = ${field.value},${field_desc(field)}
        % endfor
    };
    % endfor
    //define structs
    % for _, struct_type in all.structs.items():
    % if len(struct_type.bases) > 0:
    struct ${struct_type.code_name} : ${','.join(struct_type.bases)}
    % else:
    struct ${struct_type.code_name}
    % endif
    {
        % for field in struct_type.fields:
        ${field_type(field.type_name)} ${field_define(field)}
        % endfor

        uint32_t read(MemoryStream& stream);
    };
    % endfor
    //base structs
    % for _, base in all.bases.items():
    struct ${base.name}
    {
        % for field in base.fields:
        % if not field.in_value_map:
        ${field_type(field.type_name)} ${field_define(field)}
        % endif
        % endfor
    };
    % endfor
    //sheet structs
    % for sheet in all.sheets:
    % if sheet.base_name != '':
    struct ${sheet.name} : ${sheet.base_name}
    % else:
    struct ${sheet.name}
    % endif
    {
        % for field in sheet.self_fields:
        % if not field.in_value_map:
        ${field_type(field.type_name)} ${field_define(field)}
        % endif
        % endfor

        uint32_t read(MemoryStream& stream);
    };
    % endfor

    //enums format code
    % for _, enum_type in all.enums.items():
    REG_ENUM(${enum_type.code_name}, ${enum_type.fields_name_str});
    % endfor
}

% if len(all.enums) > 0:
namespace fmt
{
    namespace internal
    {
        % for _, enum_type in all.enums.items():
        template<> struct ConvertToInt<GameConfig::${enum_type.code_name}> { enum { value = 0 }; };
        % endfor
    }
}
% endif