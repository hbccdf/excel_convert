using System.Collections.Generic;
using Hunter;
using UnityEngine;

// ReSharper disable IdentifierTypo
// ReSharper disable CollectionNeverQueried.Global
// ReSharper disable JoinDeclarationAndInitializer
// ReSharper disable MemberCanBePrivate.Global
// ReSharper disable ArgumentsStyleOther
// ReSharper disable InconsistentNaming
// ReSharper disable NotAccessedField.Global

namespace Generated
{
    public partial class Tables
    {
        % for sheet in all.sheets:
        % if not sheet.single:
        % if len(sheet.sub_sheets) <= 1:
        private readonly ${sheet.name}[] ${sheet.name}s;
        private readonly Dictionary<${sheet.key_field.type.code_name}, ${sheet.name}> ${sheet.name}${sheet.key_field.name.title()}Map;

        % else:
        % for sub_sheet in sheet.sub_sheets:
        private readonly ${sheet.name}[] ${sub_sheet.name}s;
        private readonly Dictionary<${sheet.key_field.type.code_name}, ${sheet.name}> ${sub_sheet.name}${sheet.key_field.name.title()}Map;
        % endfor

        % endif
        % endif
        % endfor

        % for sheet in all.sheets:
        % if sheet.single:
        % if len(sheet.sub_sheets) <= 1:
        private readonly ${sheet.name} ${sheet.member_name};

        % else:
        % for sub_sheet in sheet.sub_sheets:
        private readonly ${sheet.name} ${sub_sheet.member_name};
        % endfor

        % endif
        % endif
        % endfor

        public Tables(byte[] buffer)
        {
            var helper = new BufferHelper(buffer);
            var fullVersion = helper.ReadStr();
            int count;

            % for sheet in all.sheets:
            % for sub_sheet in sheet.sub_sheets:
            count = helper.ReadInt32();
            % if not sheet.single:
            ${sub_sheet.name}s = new ${sheet.name}[count];
            ${sub_sheet.name}${sheet.key_field.name.title()}Map = new Dictionary<${sheet.key_field.type.code_name}, ${sheet.name}>();
            if (count > 0)
            {
                for (var i = 0; i < count; ++i)
                {
                    var item = new ${sheet.name}(
                        % for i, field in enumerate(sheet.fields):
                        % if i != len(sheet.fields)-1:
                        ${field.name}: ${field.type.reader},
                        % else:
                        ${field.name}: ${field.type.reader}
                        % endif
                        % endfor
                    );

                    ${sub_sheet.name}s[i] = item;
                    ${sub_sheet.name}${sheet.key_field.name.title()}Map.Add(item.${sheet.key_field.name}, item);
                }
            }
            % else:
            if (count > 0)
            {
                var item = new ${sheet.name}(
                    % for i, field in enumerate(sheet.fields):
                    % if i != len(sheet.fields)-1:
                    ${field.name}: ${field.type.reader},
                    % else:
                    ${field.name}: ${field.type.reader}
                    % endif
                    % endfor
                );

                ${sub_sheet.member_name} = item;
            }
            % endif
            % endfor
            % endfor
        }


        % for sheet in all.singles:
        % if len(sheet.sub_sheets) <= 1:
        public ${sheet.name} Get${sheet.short_name}()
        {
            return ${sheet.member_name};
        }
        % else:
        public ${sheet.name} Get${sheet.short_name}()
        {
            if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_MOBA)
            {
                return ${sheet.get_sub_sheet_by_config_type(1).member_name};
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_DIAMOND)
            {
                return ${sheet.get_sub_sheet_by_config_type(2).member_name};
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_FLY)
            {
                return ${sheet.get_sub_sheet_by_config_type(3).member_name};
            }
            return ${sheet.get_sub_sheet_by_config_type(0).member_name};
        }
        % endif
        % endfor

        % for sheet in all.not_singles:
        % if len(sheet.sub_sheets) <= 1:
        public ${sheet.name} Get${sheet.short_name}(int Id)
        {
            ${sheet.name} ret = null;
            var configMap = ${sheet.name}${sheet.key_field.name.title()}Map;

            if (!configMap.TryGetValue(Id, out ret))
            {
                ("Can't find ${sheet.name} by id " + Id).LogError();
            }

            return ret;
        }
        % else:
        public ${sheet.name} Get${sheet.short_name}(int Id)
        {
            ${sheet.name} ret = null;
            var configMap = ${sheet.get_sub_sheet_by_config_type(0).name}${sheet.key_field.name.title()}Map;
            if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_MOBA)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(1).name}${sheet.key_field.name.title()}Map;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_DIAMOND)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(2).name}${sheet.key_field.name.title()}Map;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_FLY)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(3).name}${sheet.key_field.name.title()}Map;
            }

            if (!configMap.TryGetValue(Id, out ret))
            {
                ("Can't find ${sheet.name} by id " + Id).LogError();
            }

            return ret;
        }
        % endif
        % endfor


        % for sheet in all.sheets:
        % if not sheet.single:
        % if len(sheet.sub_sheets) <= 1:
        public Dictionary<${sheet.key_field.type.code_name}, ${sheet.name}> Get${sheet.name}Map()
        {
            return ${sheet.name}${sheet.key_field.name.title()}Map;
        }
        % else:
        public Dictionary<${sheet.key_field.type.code_name}, ${sheet.name}> Get${sheet.name}Map()
        {
            var configMap = ${sheet.get_sub_sheet_by_config_type(0).name}${sheet.key_field.name.title()}Map;
            if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_MOBA)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(1).name}${sheet.key_field.name.title()}Map;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_DIAMOND)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(2).name}${sheet.key_field.name.title()}Map;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_FLY)
            {
                configMap = ${sheet.get_sub_sheet_by_config_type(3).name}${sheet.key_field.name.title()}Map;
            }

            return configMap;
        }
        % endif
        % endif
        % endfor


        % for sheet in all.sheets:
        % if not sheet.single:
        % if len(sheet.sub_sheets) <= 1:
        public ${sheet.name}[] Get${sheet.name}List()
        {
            return ${sheet.name}s;
        }
        % else:
        public ${sheet.name}[] Get${sheet.name}List()
        {
            var configList = ${sheet.get_sub_sheet_by_config_type(0).name}s;
            if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_MOBA)
            {
                configList = ${sheet.get_sub_sheet_by_config_type(1).name}s;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_DIAMOND)
            {
                configList = ${sheet.get_sub_sheet_by_config_type(2).name}s;
            }
            else if(Main.Instance.GameMode == CommonDef.ERoomCoreType.ERT_FLY)
            {
                configList = ${sheet.get_sub_sheet_by_config_type(3).name}s;
            }

            return configList;
        }
        % endif
        % endif
        % endfor
    }

    % for sheet in all.sheets:
    public class ${sheet.name}
    {
        % for field in sheet.fields:
        public readonly ${field.type.code_name} ${field.name};
        % endfor

        public ${sheet.name}(
            % for i, field in enumerate(sheet.fields):
            % if i == 0:
            ${field.type.code_name} ${field.name}
            % else:
            , ${field.type.code_name} ${field.name}
            % endif
            % endfor
        ) {
            % for field in sheet.fields:
            this.${field.name} = ${field.name};
            % endfor
        }
    };
    % endfor
}