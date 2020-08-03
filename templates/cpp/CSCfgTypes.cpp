#include "CSCfgTypes.h"
#include "ConfigUtil.h"
<%def name='output_struct(struct_type)'>\
uint32_t ${struct_type.name}::read(MemoryStream& stream)
    {
        return read_struct(stream, [this, &stream](TType ftype, int16_t fid) {
            uint32_t xfer = 0;
            switch(fid)
            {
            //foreach all field by position
            % for field in struct_type.fields:
            % if not field.only_define and not field.in_value_map:
            % if field.type.reader and field.type.reader.strip() != '':
            case ${field.position}: { ${field.type.reader}; break; } //${field.name}
            % else:
            case ${field.position}: { xfer += stream.ReadObject(ftype, this->${field.name}, ${field.is_required_str}); break; } //${field.name}
            % endif
            % endif
            % endfor
            default:
                xfer += stream.skip(ftype);
                break;
            }
            return xfer;
        });
    }\
</%def>\

namespace GameConfig
{
    uint32_t read_struct(MemoryStream& stream, std::function<uint32_t(TType, int16_t)> func)
    {
        RecursionTracker tracker(stream);
        uint32_t xfer = 0;
        std::string fname;
        TType ftype;
        int16_t fid;
        xfer += stream.ReadStructBegin(fname);

        while(true)
        {
            xfer += stream.ReadFieldBegin(fname, ftype, fid);
            if (ftype == T_STOP)
                break;

            xfer += func(ftype, fid);
            xfer += stream.ReadFieldEnd();
        }
        return xfer;
    }

    //define structs
    % for _, struct_type in all.structs.items():
    ${output_struct(struct_type)}
    % endfor
    //sheet structs
    % for sheet in all.sheets:
    ${output_struct(sheet)}
    % endfor
}