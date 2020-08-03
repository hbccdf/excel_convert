#pragma once
#include <string>
#include <vector>
#include <type_traits>
#include <network/traits/traits.hpp>
using namespace std;

namespace GameConfig
{

    template <typename To, typename From>
    static inline To bitwise_cast(From from) {
        _ASSERT(sizeof(From) == sizeof(To));

        // BAD!!!  These are all broken with -O2.
        //return *reinterpret_cast<To*>(&from);  // BAD!!!
        //return *static_cast<To*>(static_cast<void*>(&from));  // BAD!!!
        //return *(To*)(void*)&from;  // BAD!!!

        // Super clean and paritally blessed by section 3.9 of the standard.
        //unsigned char c[sizeof(from)];
        //memcpy(c, &from, sizeof(from));
        //To to;
        //memcpy(&to, c, sizeof(c));
        //return to;

        // Slightly more questionable.
        // Same code emitted by GCC.
        //To to;
        //memcpy(&to, &from, sizeof(from));
        //return to;

        // Technically undefined, but almost universally supported,
        // and the most efficient implementation.
        union {
            From f;
            To t;
        } u;
        u.f = from;
        return u.t;
    }
    enum TType {
        T_BEGIN = -1,
        T_STOP = 0,
        T_VOID = 1,
        T_BOOL = 2,
        T_BYTE = 3,
        T_I08 = 3,
        T_I16 = 6,
        T_I32 = 8,
        T_U64 = 9,
        T_I64 = 10,
        T_FLOAT = 4,
        T_DOUBLE = 5,
        T_STRING = 11,
        T_UTF7 = 11,
        T_STRUCT = 12,
        T_MAP = 13,
        T_SET = 14,
        T_LIST = 15,
        T_ARRAY = 16,
        T_UTF8 = 17,
        T_UTF16 = 18,
        T_END = 19,
    };

    static const uint32_t DEFAULT_RECURSION_LIMIT = 8;
    static const int32_t MAX_CONTAINER_SIZE = 100000;
    static const int32_t MAX_STRING_SIZE = 0;

    class MemoryStream
    {
    public:
        MemoryStream(const char* buffer, int length)
        {
            this->buffer_ = buffer;
            this->length_ = length;
            this->position_ = 0;
        }

        uint32_t ReadTableBegin(std::string& name, uint32_t& size, uint32_t& byte_length)
        {
            uint32_t result = 0;
            int32_t sizei = 0;
            int32_t bytesi = 0;
            result += ReadString(name);
            result += ReadInt32(sizei);
            result += ReadInt32(bytesi);
            CheckSize(sizei);
            size = (uint32_t)sizei;
            byte_length = (uint32_t)bytesi;
            return result;
        }

        uint32_t ReadTableEnd()
        {
            return 0;
        }

        uint32_t ReadStructBegin(std::string& name)
        {
            name = "";
            return 0;
        }

        uint32_t ReadStructEnd()
        {
            return 0;
        }

        uint32_t ReadFieldBegin(std::string& name, TType& fieldType, int16_t& fieldId)
        {
            (void)name;
            uint32_t result = 0;
            int8_t type;
            result += ReadByte(type);
            fieldType = (TType)type;
            if (fieldType == T_STOP) {
                fieldId = 0;
                return result;
            }
            result += ReadInt16(fieldId);
            return result;
        }

        uint32_t ReadFieldEnd()
        {
            return 0;
        }

        uint32_t ReadMapBegin(TType& keyType, TType& valType, uint32_t& size)
        {
            int8_t k, v;
            uint32_t result = 0;
            int32_t sizei;
            result += ReadByte(k);
            keyType = (TType)k;
            result += ReadByte(v);
            valType = (TType)v;
            result += ReadInt32(sizei);
            CheckSize(sizei);
            size = (uint32_t)sizei;
            return result;
        }

        uint32_t ReadMapEnd()
        {
            return 0;
        }

        uint32_t ReadListBegin(TType& elemType, uint32_t& size)
        {
            int8_t e;
            uint32_t result = 0;
            int32_t sizei;
            result += ReadByte(e);
            elemType = (TType)e;
            result += ReadInt32(sizei);
            CheckSize(sizei);
            size = (uint32_t)sizei;
            return result;
        }

        uint32_t ReadListEnd()
        {
            return 0;
        }

        uint32_t ReadSetBegin(TType& elemType, uint32_t& size)
        {
            int8_t e;
            uint32_t result = 0;
            int32_t sizei;
            result += ReadByte(e);
            elemType = (TType)e;
            result += ReadInt32(sizei);
            CheckSize(sizei);
            size = (uint32_t)sizei;
            return result;
        }

        uint32_t ReadSetEnd()
        {
            return 0;
        }

        uint32_t ReadArrayBegin(TType& elemType, uint32_t& size)
        {
            int8_t e;
            uint32_t result = 0;
            int32_t sizei;
            result += ReadByte(e);
            elemType = (TType)e;
            result += ReadInt32(sizei);
            CheckSize(sizei);
            size = (uint32_t)sizei;
            return result;
        }

        uint32_t ReadArrayEnd()
        {
            return 0;
        }

        uint32_t ReadBool(bool& value)
        {
            uint8_t b[1];
            ReadAll(b, 1);
            value = *(int8_t*)b != 0;
            return 1;
        }

        uint32_t ReadByte(int8_t& byte)
        {
            uint8_t b[1];
            ReadAll(b, 1);
            byte = *(int8_t*)b;
            return 1;
        }

        uint32_t ReadInt16(int16_t& i16)
        {
            union bytes {
                uint8_t b[2];
                int16_t all;
            } theBytes;
            ReadAll(theBytes.b, 2);
            i16 = theBytes.all;
            return 2;
        }

        uint32_t ReadInt32(int32_t& i32)
        {
            union bytes {
                uint8_t b[4];
                int32_t all;
            } theBytes;
            ReadAll(theBytes.b, 4);
            i32 = theBytes.all;
            return 4;
        }

        uint32_t ReadInt64(int64_t& i64)
        {
            union bytes {
                uint8_t b[8];
                int64_t all;
            } theBytes;
            ReadAll(theBytes.b, 8);
            i64 = theBytes.all;
            return 8;
        }

        uint32_t ReadFloat(float& value)
        {
            union bytes {
                uint8_t b[4];
                uint32_t all;
            } theBytes;
            ReadAll(theBytes.b, 4);
            value = bitwise_cast<float>(theBytes.all);
            return 4;
        }

        uint32_t ReadDouble(double& value)
        {
            union bytes {
                uint8_t b[8];
                uint64_t all;
            } theBytes;
            ReadAll(theBytes.b, 8);
            value = bitwise_cast<double>(theBytes.all);
            return 8;
        }

        uint32_t ReadString(std::string& str)
        {
            uint32_t result;
            int32_t size;
            result = ReadInt32(size);
            return result + ReadStringBody(str, size);
        }

        uint32_t ReadBinary(std::string& str)
        {
            return ReadString(str);
        }


        //-------------------------
        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, bool>::value, uint32_t>
        {
            if (ftype == T_BOOL)
                return ReadBool(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, int8_t>::value, uint32_t>
        {
            if (ftype == T_BYTE)
                return ReadByte(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, int16_t>::value, uint32_t>
        {
            if (ftype == T_I16)
                return ReadInt16(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, int32_t>::value, uint32_t>
        {
            if (ftype == T_I32)
                return ReadInt32(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, int64_t>::value, uint32_t>
        {
            if (ftype == T_I64)
                return ReadInt64(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, float>::value, uint32_t>
        {
            if (ftype == T_FLOAT)
                return ReadFloat(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, double>::value, uint32_t>
        {
            if (ftype == T_DOUBLE)
                return ReadDouble(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_same<T, std::string>::value, uint32_t>
        {
            if (ftype == T_STRING)
                return ReadString(field);
            else
                return skip(ftype);
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<std::is_enum<T>::value, uint32_t>
        {
            uint32_t xfer = 0;
            if (ftype == T_I32)
            {
                int32_t ecast;
                xfer += ReadInt32(ecast);
                field = (T)ecast;
            }
            else
            {
                xfer += skip(ftype);
            }
            return xfer;
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<cytx::is_vector<T>::value, uint32_t>
        {
            uint32_t xfer = 0;

            if (ftype == T_LIST)
            {
                field.clear();
                uint32_t list_size = 0;
                TType etype;
                xfer += ReadListBegin(etype, list_size);
                field.resize(list_size);
                for (uint32_t i = 0; i < list_size; ++i)
                {
                    xfer += ReadObject(etype, field[i], is_required);
                }
                xfer += ReadListEnd();
            }
            else
            {
                xfer = skip(ftype);
            }
            return xfer;
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<cytx::is_set<T>::value, uint32_t>
        {
            using element_t = decltype(*t.begin());
            using ele_t = std::remove_cv_t<std::remove_reference_t<element_t>>;

            uint32_t xfer = 0;

            if (ftype == T_SET)
            {
                field.clear();
                uint32_t list_size = 0;
                TType etype;
                xfer += ReadSetBegin(etype, list_size);
                field.resize(list_size);
                for (uint32_t i = 0; i < list_size; ++i)
                {
                    ele_t el{};
                    xfer += ReadObject(etype, el, is_required);
                    field.insert(el);
                }
                xfer += ReadSetEnd();
            }
            else
            {
                xfer = skip(ftype);
            }
            return xfer;
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<cytx::is_std_array<T>::value, uint32_t>
        {
            using element_t = decltype(*t.begin());
            using ele_t = std::remove_cv_t<std::remove_reference_t<element_t>>;

            uint32_t xfer = 0;

            if (ftype == T_LIST)
            {
                uint32_t list_size = 0;
                TType etype;
                xfer += ReadArrayBegin(etype, list_size);
                for (uint32_t i = 0; i < list_size && i < (uint32_t)field.size(); ++i)
                {
                    if (i < list_size)
                    {
                        xfer += ReadObject(etype, field[i], is_required);
                    }
                    else
                    {
                        field[i] = ele_t{};
                    }
                }
                xfer += ReadArrayEnd();
            }
            else
            {
                xfer = skip(ftype);
            }
            return xfer;
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<cytx::is_map<T>::value, uint32_t>
        {
            using element_t = decltype(*field.begin());
            using pair_t = std::remove_cv_t<std::remove_reference_t<element_t>>;
            using first_type = std::remove_cv_t<typename pair_t::first_type>;
            using second_type = typename pair_t::second_type;

            uint32_t xfer = 0;

            if (ftype == T_MAP)
            {
                field.clear();
                uint32_t list_size = 0;
                TType keytype, valtype;
                xfer += ReadMapBegin(keytype, valtype, list_size);
                for (uint32_t i = 0; i < list_size; ++i)
                {
                    first_type key{};
                    xfer += ReadObject(keytype, key, is_required);
                    auto& val = field[key];
                    xfer += ReadObject(valtype, val, is_required);
                }
                xfer += ReadMapEnd();
            }
            else
            {
                xfer = skip(ftype);
            }
            return xfer;
        }

        template<typename T>
        auto ReadObject(TType ftype, T& field, bool is_required) -> std::enable_if_t<cytx::is_user_class<T>::value, uint32_t>
        {
            uint32_t xfer = 0;
            if (ftype == T_STRUCT)
            {
                xfer += field.read(*this);
            }
            else
            {
                xfer += skip(ftype);
            }
            return xfer;
        }


        //-------------------------


        bool ReadBool()
        {
            _ASSERT(position_ + 1 <= length_);
            return this->buffer_[position_++] != 0;
        }

        int ReadInt32() {
            _ASSERT(position_ + 4 <= length_);

            int val;
            memcpy(reinterpret_cast<char*>(&val), buffer_ + position_, 4);
            position_ += 4;
            return val;
        }

        float ReadFloat() {
            _ASSERT(position_ + 4 <= length_);

            float val;
            memcpy(reinterpret_cast<char*>(&val), buffer_ + position_, 4);
            position_ += 4;
            return val;
        }

        string ReadStr()
        {
            int length = ReadInt32();
            _ASSERT(position_ + length <= length_);
            string&& val = string(buffer_ + position_, length);
            position_ += length;
            return val;
        }

        vector<int> ReadInt32List() {
            int length = ReadInt32();
            _ASSERT(position_ + length * 4 <= length_);
            vector<int>&& val = vector<int>();

            for (int i = 0; i < length; ++i)
            {
                val.push_back(ReadInt32());
            }

            return val;
        }

        vector<float> ReadFloatList() {
            int length = ReadInt32();
            _ASSERT(position_ + length * 4 <= length_);
            vector<float>&& val = vector<float>();

            for (int i = 0; i < length; ++i)
            {
                val.push_back(ReadFloat());
            }

            return val;
        }

        vector<string> ReadStrList() {
            int length = ReadInt32();
            vector<string>&& val = vector<string>();

            for (int i = 0; i < length; ++i)
            {
                val.push_back(ReadStr());
            }

            return val;
        }

        void IncreaseRecursionDepth()
        {
            ++recursion_depth_;
            if (DEFAULT_RECURSION_LIMIT < recursion_depth_)
            {
                //throw exception
            }
        }

        void DecreaseRecursionDepth()
        {
            --recursion_depth_;
        }

        uint32_t skip(TType type)
        {
            switch (type)
            {
            case T_BOOL:
            {
                bool boolv;
                return ReadBool(boolv);
            }
            case T_BYTE:
            {
                int8_t bytev;
                return ReadByte(bytev);
            }
            case T_I16:
            {
                int16_t i16;
                return ReadInt16(i16);
            }
            case T_I32:
            {
                int32_t i32;
                return ReadInt32(i32);
            }
            case T_I64:
            {
                int64_t i64;
                return ReadInt64(i64);
            }
            case T_FLOAT:
            {
                float fv;
                return ReadFloat(fv);
            }
            case T_DOUBLE:
            {
                double dv;
                return ReadDouble(dv);
            }
            case T_STRING:
            {
                std::string str;
                return ReadBinary(str);
            }
            case T_STRUCT:
            {
                uint32_t result = 0;
                std::string name;
                int16_t fid;
                TType ftype;
                result += ReadStructBegin(name);
                while (true)
                {
                    result += ReadFieldBegin(name, ftype, fid);
                    if (ftype == T_STOP)
                        break;
                    result += skip(ftype);
                    result += ReadFieldEnd();
                }
                result += ReadStructEnd();
                return result;
            }
            case T_MAP:
            {
                uint32_t result = 0;
                TType keyType;
                TType valType;
                uint32_t i, size;
                result += ReadMapBegin(keyType, valType, size);
                for (i = 0; i < size; ++i)
                {
                    result += skip(keyType);
                    result += skip(valType);
                }
                result += ReadMapEnd();
                return result;
            }
            case T_SET:
            {
                uint32_t result = 0;
                TType elemType;
                uint32_t i, size;
                result += ReadSetBegin(elemType, size);
                for (i = 0; i < size; i++) {
                    result += skip(elemType);
                }
                result += ReadSetEnd();
                return result;
            }
            case T_LIST:
            {
                uint32_t result = 0;
                TType elemType;
                uint32_t i, size;
                result += ReadListBegin(elemType, size);
                for (i = 0; i < size; i++) {
                    result += skip(elemType);
                }
                result += ReadListEnd();
                return result;
            }
            case T_ARRAY:
            {
                uint32_t result = 0;
                TType elemType;
                uint32_t i, size;
                result += ReadArrayBegin(elemType, size);
                for (i = 0; i < size; i++) {
                    result += skip(elemType);
                }
                result += ReadArrayEnd();
                return result;
            }
            case T_STOP:
            case T_VOID:
            case T_U64:
            case T_UTF8:
            case T_UTF16:
                break;
            }

            return 0;
        }

        void Consume(uint32_t size)
        {
            _ASSERT(position_ + size <= length_);
            position_ += size;
        }

        bool IsEnd() const
        {
            return position_ >= length_;
        }

    private:
        void CheckSize(int32_t size)
        {
            if (size < 0)
            {
                throw std::exception("invalid size");
            }
            else if (size > MAX_CONTAINER_SIZE)
            {
                throw std::exception("too max size");
            }
        }

        void ReadAll(uint8_t* buffer, int32_t size)
        {
            _ASSERT(position_ + size <= length_);

            std::memcpy(buffer, buffer_ + position_, size);
            position_ += size;
        }

        uint32_t ReadStringBody(std::string& str, int32_t size)
        {
            uint32_t result = 0;

            // Catch error cases
            if (size < 0) {
                //invalid size
            }
            if (MAX_STRING_SIZE > 0 && size > MAX_STRING_SIZE) {
                // to max size
            }

            // Catch empty string case
            if (size == 0) {
                str.clear();
                return result;
            }

            str.resize(size);
            ReadAll(reinterpret_cast<uint8_t*>(&str[0]), size);
            return (uint32_t)size;
        }

    private:

        const char* buffer_;
        uint32_t length_;
        uint32_t position_;
        uint32_t recursion_depth_ = 0;
    };

    class RecursionTracker
    {
    public:
        RecursionTracker(MemoryStream& stream)
            : stream_(stream)
        {
            stream_.IncreaseRecursionDepth();
        }

        ~RecursionTracker()
        {
            stream_.DecreaseRecursionDepth();
        }

    private:
        MemoryStream& stream_;
    };
}
