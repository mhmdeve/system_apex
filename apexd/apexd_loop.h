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

#ifndef ANDROID_APEXD_APEXD_LOOP_H_
#define ANDROID_APEXD_APEXD_LOOP_H_

#include <android-base/result.h>
#include <android-base/unique_fd.h>

#include <functional>
#include <string>

namespace android {
namespace apex {
namespace loop {

using android::base::unique_fd;

struct LoopbackDeviceUniqueFd {
  unique_fd device_fd;
  std::string name;

  LoopbackDeviceUniqueFd() {}
  LoopbackDeviceUniqueFd(unique_fd&& fd, const std::string& name)
      : device_fd(std::move(fd)), name(name) {}

  LoopbackDeviceUniqueFd(LoopbackDeviceUniqueFd&& fd) noexcept
      : device_fd(std::move(fd.device_fd)), name(std::move(fd.name)) {}
  LoopbackDeviceUniqueFd& operator=(LoopbackDeviceUniqueFd&& other) noexcept {
    MaybeCloseBad();
    device_fd = std::move(other.device_fd);
    name = std::move(other.name);
    return *this;
  }

  ~LoopbackDeviceUniqueFd() { MaybeCloseBad(); }

  void MaybeCloseBad();

  void CloseGood() { device_fd.reset(-1); }

  int Get() { return device_fd.get(); }
};

android::base::Result<LoopbackDeviceUniqueFd> WaitForDevice(int num);

android::base::Result<void> ConfigureReadAhead(const std::string& device_path);

android::base::Result<void> PreAllocateLoopDevices(size_t num);

android::base::Result<LoopbackDeviceUniqueFd> CreateAndConfigureLoopDevice(
    const std::string& target, uint32_t image_offset, size_t image_size);

void FinishConfiguring(const std::string& loop_device,
                       const std::string& backing_file);

using DestroyLoopFn =
    std::function<void(const std::string&, const std::string&)>;
void DestroyLoopDevice(const std::string& path, const DestroyLoopFn& extra);

}  // namespace loop
}  // namespace apex
}  // namespace android

#endif  // ANDROID_APEXD_APEXD_LOOP_H_
