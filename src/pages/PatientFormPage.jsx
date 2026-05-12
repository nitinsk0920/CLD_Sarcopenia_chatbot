import { useNavigate } from "react-router-dom";
import { useState } from "react";
import AppLayout from "../components/AppLayout";
import { normalizeLanguageCode, useLanguage } from "../i18n/LanguageContext";
import { getPatientFormOverride } from "../i18n/patientFormOverrides";

const genderOptions = ["male", "female", "other"];
const educationalQualificationOptions = [
  "noFormalEducation",
  "primaryEducation",
  "secondaryEducation",
  "higherSecondary",
  "graduateAndAbove",
];
const occupationOptions = ["employed", "unemployed", "homemaker", "retired"];
const yesNoNotSureOptions = ["yes", "no", "notSure"];
const yesNoOptions = ["yes", "no"];
const dietOptions = ["vegetarian", "nonVegetarian", "mixed"];
const appetiteOptions = ["normal", "lowAppetite"];
const proteinOptions = ["enoughProtein", "notEnoughProtein", "unsureProtein"];
const exerciseTypeOptions = ["walking", "stretching", "strength", "noneExercise"];
const exerciseFrequencyOptions = ["daily", "sometimes", "never"];
const languageOptions = ["en", "kn", "hi", "mr"];
const symptomOptions = [
  "weakness",
  "muscleLoss",
  "dizziness",
  "lowEnergy",
  "swelling",
  "poorSleep",
  "appetiteLoss",
];
const habitOptions = ["alcohol", "smoking", "tobacco"];

function SectionCard({ title, helpText, children }) {
  return (
    <section className="question-card">
      <div className="mb-5 border-b border-hospital-200 pb-4">
        <h2 className="text-xl font-semibold text-hospital-900">{title}</h2>
        {helpText ? <p className="mt-1 text-sm text-hospital-700">{helpText}</p> : null}
      </div>
      <div className="grid gap-5">{children}</div>
    </section>
  );
}

function FieldPanel({ children, wide = false }) {
  return <div className={`form-panel ${wide ? "form-panel-wide" : ""}`}>{children}</div>;
}

export default function PatientFormPage({ patient, setPatient, onSessionStart }) {
  const navigate = useNavigate();
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const { t, setLanguage, language } = useLanguage();

  function pf(path) {
    return getPatientFormOverride(language, path) ?? t(path);
  }

  function handleChange(event) {
    const { name, value } = event.target;

    if (name === "languagePreference") {
      setLanguage(value);
    }

    setPatient((prev) => ({ ...prev, [name]: value }));
  }

  function handleCheckboxGroupChange(name, value, checked) {
    setPatient((prev) => {
      const currentItems = Array.isArray(prev[name]) ? prev[name] : [];
      const nextItems = checked
        ? [...currentItems, value]
        : currentItems.filter((item) => item !== value);

      return { ...prev, [name]: nextItems };
    });
  }

  function validate() {
    const nextErrors = {};

    if (!patient.patientId) nextErrors.patientId = pf("patientForm.errors.patientId");
    if (!patient.age) nextErrors.age = pf("patientForm.errors.age");
    if (!patient.gender) nextErrors.gender = pf("patientForm.errors.gender");
    if (!patient.educationalQualification) {
      nextErrors.educationalQualification = pf("patientForm.errors.educationalQualification");
    }
    if (!patient.occupation) {
      nextErrors.occupation = pf("patientForm.errors.occupation");
    }
    if (!patient.cldStatus) nextErrors.cldStatus = pf("patientForm.errors.cldStatus");
    if (!patient.weaknessFatigue) {
      nextErrors.weaknessFatigue = pf("patientForm.errors.weaknessFatigue");
    }
    if (!patient.recentWeightLoss) {
      nextErrors.recentWeightLoss = pf("patientForm.errors.recentWeightLoss");
    }
    if (!patient.dietType) nextErrors.dietType = pf("patientForm.errors.dietType");
    if (!patient.appetiteLevel) nextErrors.appetiteLevel = pf("patientForm.errors.appetiteLevel");
    if (!patient.proteinAwareness) {
      nextErrors.proteinAwareness = pf("patientForm.errors.proteinAwareness");
    }
    if (!patient.exerciseRegular) {
      nextErrors.exerciseRegular = pf("patientForm.errors.exerciseRegular");
    }
    if (!patient.exerciseType) nextErrors.exerciseType = pf("patientForm.errors.exerciseType");
    if (!patient.exerciseFrequency) {
      nextErrors.exerciseFrequency = pf("patientForm.errors.exerciseFrequency");
    }
    if (!patient.languagePreference) {
      nextErrors.languagePreference = pf("patientForm.errors.languagePreference");
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError("");
    if (!validate()) return;

    if (onSessionStart) {
      const result = await onSessionStart(patient);
      if (!result?.success) {
        setSubmitError(result?.error || "Could not start the patient session.");
        return;
      }
    }

    navigate("/pre-test");
  }

  return (
    <AppLayout
      title={pf("patientForm.title")}
      subtitle={pf("patientForm.subtitle")}
      backTo="/welcome"
    >
      <form onSubmit={handleSubmit} className="stack">
        <SectionCard
          title={t("patientForm.basicInfoTitle")}
          helpText={pf("patientForm.basicInfoHelp")}
        >
          <div className="form-section-grid">
            <FieldPanel>
              <label className="field">
                <span>{pf("patientForm.patientId")}</span>
                <input
                  type="text"
                  name="patientId"
                  value={patient.patientId}
                  onChange={handleChange}
                  placeholder={pf("patientForm.patientIdPlaceholder")}
                  required
                />
                {errors.patientId ? <small className="error-text">{errors.patientId}</small> : null}
              </label>
            </FieldPanel>

            <FieldPanel>
              <label className="field">
                <span>{pf("patientForm.age")}</span>
                <input
                  type="number"
                  name="age"
                  min="1"
                  max="120"
                  value={patient.age}
                  onChange={handleChange}
                  placeholder={pf("patientForm.agePlaceholder")}
                  required
                />
                {errors.age ? <small className="error-text">{errors.age}</small> : null}
              </label>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.gender")}</span>
                <div className="choice-grid choice-grid-three">
                  {genderOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="gender"
                        value={item}
                        checked={patient.gender === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.gender ? <small className="error-text">{errors.gender}</small> : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.educationalQualification")}</span>
                <div className="choice-grid choice-grid-three">
                  {educationalQualificationOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="educationalQualification"
                        value={item}
                        checked={patient.educationalQualification === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.educationalQualification ? (
                  <small className="error-text">{errors.educationalQualification}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.occupation")}</span>
                <div className="choice-grid choice-grid-four">
                  {occupationOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="occupation"
                        value={item}
                        checked={patient.occupation === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.occupation ? (
                  <small className="error-text">{errors.occupation}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.healthStatusTitle")}
          helpText={pf("patientForm.healthStatusHelp")}
        >
          <div className="form-section-grid">
            <FieldPanel>
              <fieldset className="field">
                <span>{t("patientForm.cldStatus")}</span>
                <div className="choice-grid choice-grid-three">
                  {yesNoNotSureOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="cldStatus"
                        value={item}
                        checked={patient.cldStatus === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.cldStatus ? <small className="error-text">{errors.cldStatus}</small> : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <label className="field">
                <span>{pf("patientForm.illnessDuration")}</span>
                <input
                  type="text"
                  name="illnessDuration"
                  value={patient.illnessDuration}
                  onChange={handleChange}
                  placeholder={pf("patientForm.illnessDurationPlaceholder")}
                />
              </label>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.weaknessFatigue")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="weaknessFatigue"
                        value={item}
                        checked={patient.weaknessFatigue === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.weaknessFatigue ? (
                  <small className="error-text">{errors.weaknessFatigue}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.recentWeightLoss")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="recentWeightLoss"
                        value={item}
                        checked={patient.recentWeightLoss === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.recentWeightLoss ? (
                  <small className="error-text">{errors.recentWeightLoss}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard title={pf("patientForm.dietTitle")} helpText={pf("patientForm.dietHelp")}>
          <div className="form-section-grid">
            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.dietType")}</span>
                <div className="choice-grid choice-grid-three">
                  {dietOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="dietType"
                        value={item}
                        checked={patient.dietType === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.dietType ? <small className="error-text">{errors.dietType}</small> : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.appetiteLevel")}</span>
                <div className="choice-grid choice-grid-two">
                  {appetiteOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="appetiteLevel"
                        value={item}
                        checked={patient.appetiteLevel === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.appetiteLevel ? (
                  <small className="error-text">{errors.appetiteLevel}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel wide>
              <fieldset className="field">
                <span>{pf("patientForm.proteinAwareness")}</span>
                <div className="choice-grid choice-grid-three">
                  {proteinOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="proteinAwareness"
                        value={item}
                        checked={patient.proteinAwareness === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.proteinAwareness ? (
                  <small className="error-text">{errors.proteinAwareness}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.exerciseTitle")}
          helpText={pf("patientForm.exerciseHelp")}
        >
          <div className="form-section-grid-3">
            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseRegular")}</span>
                <div className="choice-grid choice-grid-two">
                  {yesNoOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseRegular"
                        value={item}
                        checked={patient.exerciseRegular === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseRegular ? (
                  <small className="error-text">{errors.exerciseRegular}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseType")}</span>
                <div className="choice-grid choice-grid-two">
                  {exerciseTypeOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseType"
                        value={item}
                        checked={patient.exerciseType === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseType ? (
                  <small className="error-text">{errors.exerciseType}</small>
                ) : null}
              </fieldset>
            </FieldPanel>

            <FieldPanel>
              <fieldset className="field">
                <span>{pf("patientForm.exerciseFrequency")}</span>
                <div className="choice-grid choice-grid-three">
                  {exerciseFrequencyOptions.map((item) => (
                    <label key={item} className="choice-item">
                      <input
                        type="radio"
                        name="exerciseFrequency"
                        value={item}
                        checked={patient.exerciseFrequency === item}
                        onChange={handleChange}
                      />
                      <span>{pf(`patientForm.options.${item}`)}</span>
                    </label>
                  ))}
                </div>
                {errors.exerciseFrequency ? (
                  <small className="error-text">{errors.exerciseFrequency}</small>
                ) : null}
              </fieldset>
            </FieldPanel>
          </div>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.symptomsTitle")}
          helpText={pf("patientForm.symptomsHelp")}
        >
          <FieldPanel>
            <fieldset className="field">
              <span>{pf("patientForm.symptoms")}</span>
              <div className="choice-grid choice-grid-four">
                {symptomOptions.map((item) => (
                  <label key={item} className="choice-item">
                    <input
                      type="checkbox"
                      checked={patient.symptoms.includes(item)}
                      onChange={(event) =>
                        handleCheckboxGroupChange("symptoms", item, event.target.checked)
                      }
                    />
                    <span>{pf(`patientForm.options.${item}`)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </FieldPanel>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.lifestyleTitle")}
          helpText={pf("patientForm.lifestyleHelp")}
        >
          <FieldPanel>
            <fieldset className="field">
              <span>{pf("patientForm.habits")}</span>
              <div className="choice-grid choice-grid-three">
                {habitOptions.map((item) => (
                  <label key={item} className="choice-item">
                    <input
                      type="checkbox"
                      checked={patient.habits.includes(item)}
                      onChange={(event) =>
                        handleCheckboxGroupChange("habits", item, event.target.checked)
                      }
                    />
                    <span>{pf(`patientForm.options.${item}`)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </FieldPanel>
        </SectionCard>

        <SectionCard
          title={pf("patientForm.languageTitle")}
          helpText={pf("patientForm.languageHelp")}
        >
          <FieldPanel>
            <label className="field">
              <span>{pf("patientForm.languagePreference")}</span>
              <select
                name="languagePreference"
                value={patient.languagePreference ? normalizeLanguageCode(patient.languagePreference) : ""}
                onChange={handleChange}
                required
              >
                <option value="">{pf("patientForm.selectLanguage")}</option>
                {languageOptions.map((item) => (
                  <option key={item} value={item}>
                    {t(`languages.${item}`)}
                  </option>
                ))}
              </select>
              {errors.languagePreference ? (
                <small className="error-text">{errors.languagePreference}</small>
              ) : null}
            </label>
          </FieldPanel>
        </SectionCard>

        {submitError ? <p className="error-text">{submitError}</p> : null}

        <button type="submit" className="btn btn-primary btn-block">
          {pf("patientForm.submit")}
        </button>
      </form>
    </AppLayout>
  );
}
