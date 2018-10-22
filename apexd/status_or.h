/*
 * Copyright (C) 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef ANDROID_APEXD_STATUS_OR_H_
#define ANDROID_APEXD_STATUS_OR_H_

#include <string>
#include <variant>

#include <android-base/logging.h>
#include <android-base/macros.h>

namespace android {
namespace apex {

template <typename T>
class StatusOr {
 private:
  enum class StatusOrTag {
    kDummy
  };

  static constexpr std::in_place_index_t<0> kIndex0{};
  static constexpr std::in_place_index_t<1> kIndex1{};

 public:
  template <class... Args>
  explicit StatusOr(Args&&... args) : data_(kIndex1, std::forward<Args>(args)...) {}

  bool Ok() const WARN_UNUSED {
    return data_.index() != 0;
  }

  T& operator*() {
    CHECK(Ok());
    return *std::get_if<1u>(&data_);
  }

  T* operator->() {
    CHECK(Ok());
    return std::get_if<1u>(&data_);
  }

  const std::string& ErrorMessage() const {
    CHECK(!Ok());
    return *std::get_if<0u>(&data_);
  }

  static StatusOr MakeError(const std::string& msg) {
    return StatusOr(msg, StatusOrTag::kDummy);
  }

 private:
  StatusOr(const std::string& msg, StatusOrTag dummy ATTRIBUTE_UNUSED) : data_(kIndex0, msg) {}

  std::variant<std::string, T> data_;
};

}
}

#endif // ANDROID_APEXD_STATUS_OR_H_